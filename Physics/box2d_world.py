"""
Box2D Physics World -moduuli
============================
Tämä moduuli tarjoaa Box2D-fysiikkamoottorille kerrosrajapinnan (adapter pattern),
joka ylläpitää kiinteää aikaskaalausta ja synkronoi spritejen paikat fysiikkamaailmaan.

Pääkomponentit:
- CollisionCategory: Vakiot törmäysluokille (kategoriat)
- ContactCollector: Box2D-kontaktien kerääminen ja hallinta
- Box2DPhysicsWorld: Tärkein luokka, hallinnoi fysiikkamaailmaa ja entiteettejä

Käyttö:
    physics_world = Box2DPhysicsWorld()
    physics_world.add_circle_body(player, radius=20)
    physics_world.step(delta_time)
"""

import time
from collections import deque

import pygame

from Physics.box2d_config import get_physics_profile

try:
    from Box2D import (
        b2CircleShape,
        b2ContactListener,
        b2_dynamicBody,
        b2Filter,
        b2_kinematicBody,
        b2_staticBody,
        b2Vec2,
        b2World,
    )
except Exception as exc:  # pragma: no cover - handled by caller
    raise RuntimeError("Box2D is required for Box2DPhysicsWorld") from exc


# ==========================
# LUOKAN VAKIOT - TÖRMÄYSLUOKAT
# Määrittelee eri entiteettityyppien törmäysluokat Box2D-filtterille
# PALAUTTAA: Bittimaskeja käytettäväksi filterData.categoryBits ja maskBits
# ==========================
class CollisionCategory:
    PLAYER = 0x0001
    ENEMY = 0x0002
    PROJECTILE = 0x0004
    METEOR = 0x0008
    SENSOR = 0x0010


# ==========================
# ContactCollector LUOKKA
# ATTRIBUUTIT: begin_contacts (int), contact_events (deque)
# METODIT: BeginContact(), reset_frame_metrics()
# TARKOITUS: Kerää Box2D-kontaktit kerrasta ja tallentaa kontaktin osapuolet
# PALAUTTAA: Contact event -tiedot deque-listassa (max 64 tapahtumaa)
# ==========================
class ContactCollector(b2ContactListener):
    """Kerää fysiikamaailman kontaktitapahtumat kustakin framesta."""
    
    def __init__(self):
        """
        Alustaa kontaktinkeräimen.
        
        ATTRIBUUTIT:
        - begin_contacts: Kuinka monta kontaktitapahtumaa tällä framella
        - contact_events: Jonossa viimeiset 64 kontaktitapahtumaa (entity pairs)
        """
        super().__init__()
        self.begin_contacts = 0
        self.contact_events = deque(maxlen=64)

    def BeginContact(self, contact):
        """
        Kutsutaan kun kaksi kehoa alkaa koskettaa toisiaan.
        
        PARAMETRIT:
        - contact: Box2D contact-objekti, joka sisältää fixtureA ja fixtureB
        
        TOIMINTA:
        - Lisää kontaktitapahtuman jonoon (userData-objekteista)
        - Kasvattaa begin_contacts laskurin
        
        PALAUTTAA: Ei mitään (void)
        """
        self.begin_contacts += 1
        a = getattr(contact.fixtureA.body, "userData", None)
        b = getattr(contact.fixtureB.body, "userData", None)
        self.contact_events.append((a, b))

    def reset_frame_metrics(self):
        """
        Nollaa kehyksen kontaktimetriikat.
        
        TOIMINTA: Asettaa begin_contacts nollaan seuraavalle framelle
        
        PALAUTTAA: Ei mitään (void)
        """
        self.begin_contacts = 0


# ==========================
# Box2DPhysicsWorld LUOKKA
# ATTRIBUUTIT: world, profile, fixed_dt, entity_to_body, step_time_ms, jne.
# METODIT: add_circle_body(), add_static_circle(), step(), apply_explosion_impulse(), jne.
# TARKOITUS: Hallinnoi Box2D-fysiikkamaailmaa, entiteettejä ja kiinteää aikaskaalausta
# PALAUTTAA: Fysiikassa päivitetyt entiteettien paikat, nopeudet ja kulmat
# ==========================
class Box2DPhysicsWorld:
    """Small adapter that keeps Box2D in fixed-step mode and syncs sprites."""

    PPM = 30.0  # pixels per meter

    def __init__(
        self,
        gravity=(0.0, 0.0),
        fixed_dt=1.0 / 60.0,
        velocity_iterations=8,
        position_iterations=3,
        max_substeps=5,
        profile_name="balanced",
    ):
        """
        Alustaa Box2D-fysiikkamaailman kiinteällä aikaskaalalla.
        
        PARAMETRIT:
        - gravity: Painovoimavektori (x, y), oletuksena nolla
        - fixed_dt: Kiinteä aikaskaala sekunteissa (oletuksena 1/60s)
        - velocity_iterations: Box2D nopeusiteraatiot (korkeampi = tarkempi)
        - position_iterations: Box2D positioiteraatiot (korkeampi = tarkempi)
        - max_substeps: Maksimi aliaskeleita per frame
        - profile_name: "balanced" jne. fysiikkaprofiili
        
        ATTRIBUUTIT (luodaan):
        - world: Box2D World -objekti
        - contact_collector: ContactCollector -objekti
        - entity_to_body: Dict joka mapaa entiteetit Box2D-kappaleiksi
        - accumulator (aikajono): Ajan keräily kiinteää aikaaskelta varten
        - step_time_ms: Viimeksi kulunut aika millisekunteissa
        
        PALAUTTAA: Ei mitään (void)
        """
        self.profile = get_physics_profile(profile_name)
        self.fixed_dt = float(fixed_dt)
        self.velocity_iterations = int(velocity_iterations)
        self.position_iterations = int(position_iterations)
        self.max_substeps = int(max_substeps)
        self.accumulator = 0.0

        self.world = b2World(gravity=gravity, doSleep=True)
        self.contact_collector = ContactCollector()
        self.world.contactListener = self.contact_collector

        self.entity_to_body = {}

        self.step_time_ms = 0.0
        self.last_substeps = 0
        self.frame_contacts = 0

    @classmethod
    def pixels_to_meters(cls, value_px):
        """
        Muuntaa pikselit metreiksi Box2D-käyttöä varten.
        
        PARAMETRIT:
        - value_px: Arvo pikseleinä
        
        PALAUTTAA: Arvo metreinä (value_px / 30.0)
        """
        return float(value_px) / cls.PPM

    @classmethod
    def meters_to_pixels(cls, value_m):
        """
        Muuntaa metrit pikseleiksi ruudulla näyttöä varten.
        
        PARAMETRIT:
        - value_m: Arvo metreinä
        
        PALAUTTAA: Arvo pikseleinä (value_m * 30.0)
        """
        return float(value_m) * cls.PPM

    def add_circle_body(
        self,
        entity,
        radius_px,
        mass=1.0,
        dynamic=True,
        bullet=False,
        category=CollisionCategory.PLAYER,
        mask=0xFFFF,
        restitution=0.05,
        friction=0.2,
    ):
        """
        Lisää dynaamisen tai kiinteän pyöreän kehon entiteetille.
        
        PARAMETRIT:
        - entity: Sprite/objekti, jolle luodaan fysiikkakeho
        - radius_px: Kehon säde pikseleinä
        - mass: Massan tiheys (oletuksena 1.0)
        - dynamic: True = dynaaminen keho, False = kinemaattinen (vain liike, ei voimat)
        - bullet: True = luoti (nopeat objektit), False = normaali
        - category: Törmäysluokka (CollisionCategory.PLAYER jne.)
        - mask: Mihin luokkiin tämä voi törmätä (bittimaskti)
        - restitution: Pompautuvuus (0.0 = kuollut, 1.0 = täydellinen pomppaus)
        - friction: Kitka (0.0 = liukas, 1.0+ = kitkainen)
        
        LUODAAN:
        - Box2D-fysiikkakeho, joka synkronoidaan entiteettiin step()-kutsun yhteydessä
        - Synkronoidut attribuutit: entity.pos, entity.vel, entity.rect.center, entity.angle
        
        PALAUTTAA: Box2D body -objekti
        """
        x_px, y_px = self._entity_center(entity)
        body_type = b2_dynamicBody if dynamic else b2_kinematicBody
        body = self.world.CreateBody(
            type=body_type,
            position=(self.pixels_to_meters(x_px), self.pixels_to_meters(y_px)),
            bullet=bool(bullet),
            linearDamping=self.profile.linear_damping,
            angularDamping=self.profile.angular_damping,
            fixedRotation=False,
        )

        radius_m = max(0.05, self.pixels_to_meters(radius_px))
        fixture = body.CreateFixture(
            shape=b2CircleShape(radius=radius_m),
            density=max(0.001, float(mass)),
            friction=float(friction),
            restitution=float(restitution),
        )
        fixture.filterData = b2Filter(categoryBits=int(category), maskBits=int(mask), groupIndex=0)

        body.userData = entity
        self.entity_to_body[entity] = body
        return body

    def add_static_circle(
        self,
        entity,
        radius_px,
        category=CollisionCategory.METEOR,
        mask=0xFFFF,
        restitution=0.1,
        friction=0.4,
    ):
        """
        Lisää staattisen (liikkumattoman) pyöreän kehon entiteetille.
        
        PARAMETRIT:
        - entity: Sprite/objekti, jolle luodaan fysiikkakeho (ei liiku)
        - radius_px: Kehon säde pikseleinä
        - category: Törmäysluokka (oletuksena meteorit)
        - mask: Mihin luokkiin tämä voi törmätä (bittimaskti)
        - restitution: Pompautuvuus (oletuksena 0.1)
        - friction: Kitka (oletuksena 0.4)
        
        LUODAAN:
        - Staattinen fysiikkakeho, joka synkronoidaan entiteettiin step()-kutsun yhteydessä
        - Objekti ei liiku nopeuteilla, sopii kiinteille esteille ja planeeteille
        
        PALAUTTAA: Box2D body -objekti (staattinen)
        """
        x_px, y_px = self._entity_center(entity)
        body = self.world.CreateBody(
            type=b2_staticBody,
            position=(self.pixels_to_meters(x_px), self.pixels_to_meters(y_px)),
        )
        radius_m = max(0.05, self.pixels_to_meters(radius_px))
        fixture = body.CreateFixture(
            shape=b2CircleShape(radius=radius_m),
            density=1.0,
            friction=float(friction),
            restitution=float(restitution),
        )
        fixture.filterData = b2Filter(categoryBits=int(category), maskBits=int(mask), groupIndex=0)
        body.userData = entity
        self.entity_to_body[entity] = body
        return body

    def remove_entity(self, entity):
        """
        Poistaa entiteetin fysiikkamaailmasta.
        
        PARAMETRIT:
        - entity: Poistettava entiteetti
        
        TOIMINTA:
        - Hakee entiteetin Box2D-kehon
        - Tuhoaa kehon ja poistaa mappauksen
        
        PALAUTTAA: Ei mitään (void)
        """
        body = self.entity_to_body.pop(entity, None)
        if body is not None:
            self.world.DestroyBody(body)

    def get_body(self, entity):
        """
        Hakee entiteetin Box2D-kehon.
        
        PARAMETRIT:
        - entity: Entiteetti, jonka keho haetaan
        
        PALAUTTAA: Box2D body -objekti tai None jos ei löydy
        """
        return self.entity_to_body.get(entity)

    def step(self, dt_seconds):
        """
        Updates fysiikkamaailman kiinteällä aikaskaalalla ja synkronoi entiteetit.
        
        PARAMETRIT:
        - dt_seconds: Delta-aika sekunteissa edellisestä framesta
        
        TOIMINTA:
        1. Kerää delta-ajan aikajonoon
        2. Simuloi Box2D-aliaskeleita kiinteällä aikaskaalalla (max_substeps kappaa)
        3. Synkronoi kaikki entiteetit fysiikasta (pos, vel, angle)
        4. Mittaa simulaation laskentaaikaa millisekunteissa
        
        ATTRIBUUTIT (päivitetään):
        - accumulator (aikajono): Jäljellä olevaa aikaa seuraavaa aliaskelta varten
        - step_time_ms: Viimeksi kulunut simulaation aika
        - last_substeps: Kuinka monta aliaskelta suoritettiin
        - frame_contacts: Kontaktien lukumäärä
        
        PALAUTTAA: Ei mitään (void)
        """
        dt_seconds = max(0.0, float(dt_seconds))
        self.accumulator += dt_seconds

        self.contact_collector.reset_frame_metrics()
        substeps = 0
        t0 = time.perf_counter()

        while self.accumulator >= self.fixed_dt and substeps < self.max_substeps:
            self.world.Step(self.fixed_dt, self.velocity_iterations, self.position_iterations)
            self.world.ClearForces()
            self.accumulator -= self.fixed_dt
            substeps += 1

        alpha = self.accumulator / self.fixed_dt if self.fixed_dt > 0 else 0.0
        for entity, body in list(self.entity_to_body.items()):
            self._sync_entity_from_body(entity, body, alpha)

        self.step_time_ms = (time.perf_counter() - t0) * 1000.0
        self.last_substeps = substeps
        self.frame_contacts = self.contact_collector.begin_contacts

    def apply_explosion_impulse(self, center_px, radius_px, impulse_strength):
        """
        Soveltaa räjähdyksestä peräisin olevaa impulssia lähelläoleviin dynaamisiin kappaleisiin.
        
        PARAMETRIT:
        - center_px: Räjähdyksen keskipiste pikseleinä (tuple tai Vector2)
        - radius_px: Räjähdyksen vaikutusala pikseleinä (falloff-säde)
        - impulse_strength: Impulssin voimakkuus (newtonian-sekunteja)
        
        TOIMINTA:
        1. Etsii kaikki dynaamiset kappaleet säteen sisällä
        2. Laskee etäisyyteen perustuvan falloff-kertoimen (kuolleena 0-säde)
        3. Soveltaa suuntaa säde-etäisyyteen perustuva impulssijää kuhunkin kappaleeseen
        
        PALAUTTAA: Ei mitään (void)
        """
        center = pygame.Vector2(center_px)
        radius_px = max(1.0, float(radius_px))

        for body in self.entity_to_body.values():
            if body.type != b2_dynamicBody:
                continue

            pos_px = pygame.Vector2(
                self.meters_to_pixels(body.position.x),
                self.meters_to_pixels(body.position.y),
            )
            delta = pos_px - center
            dist = delta.length()
            if dist <= 1e-5 or dist > radius_px:
                continue

            direction = delta.normalize()
            falloff = max(0.0, 1.0 - (dist / radius_px))
            impulse = direction * (float(impulse_strength) * falloff)
            body.ApplyLinearImpulse(
                impulse=(self.pixels_to_meters(impulse.x), self.pixels_to_meters(impulse.y)),
                point=body.worldCenter,
                wake=True,
            )

    def get_metrics(self):
        """
        Hakee fysiikkamaailman suoritusmetriikat.
        
        PALAUTTAA: Dictionary:
        {
            'physics_step_ms': Simulaation laskentaaika millisekunteissa,
            'substeps': Kuinka monta aliaskelta tällä framella,
            'contacts': Kontaktien lukumäärä,
            'profile': Nykyisen profiilin nimi,
            'fixed_dt': Kiinteä aikaskaala (fixed delta time)
        }
        """
        return {
            "physics_step_ms": self.step_time_ms,
            "substeps": self.last_substeps,
            "contacts": self.frame_contacts,
            "profile": self.profile.name,
            "fixed_dt": self.fixed_dt,
        }

    # ==========================
    # APUMETODIT - SISÄISET METODIT
    # ==========================
    
    @staticmethod
    def _entity_center(entity):
        """
        Hakee entiteetin keskipisteen pikseleinä.
        
        PARAMETRIT:
        - entity: Entiteetti (sprite), jonka keskipiste haetaan
        
        TOIMINTA:
        1. Ensin tarkistaa entity.pos -attribuuttia
        2. Jos ei ole, käyttää entity.rect.center -attribuuttia
        3. Jos molemmat puuttuvat, palauttaa (0, 0)
        
        PALAUTTAA: Tupla (center_x, center_y) pikseleinä
        """
        if hasattr(entity, "pos"):
            p = pygame.Vector2(entity.pos)
            return p.x, p.y

        rect = getattr(entity, "rect", None)
        if rect is not None:
            return float(rect.centerx), float(rect.centery)
        return 0.0, 0.0

    def _sync_entity_from_body(self, entity, body, alpha):
        """
        Synkronoi entiteetin attribuutit Box2D-kehon tilasta.
        
        PARAMETRIT:
        - entity: Entiteetti, jota päivitetään
        - body: Box2D body -objekti, jonka tiedoista synkronoidaan
        - alpha: Interpolaatiokerroin (0.0-1.0) alikeskeille
        
        TOIMINTA:
        1. Muuntaa body.position metreistä pikseleihin
        2. Muuntaa body.linearVelocity metreistä/s pikseleihin/s
        3. Asettaa entity.pos vektorin
        4. Asettaa entity.vel nopeusvektorin
        5. Asettaa entity.rect.center paikanvektorin
        6. Asettaa entity.angle kulmaksi (Box2D radiaanit -> asteet)
        
        PALAUTTAA: Ei mitään (void)
        """
        x_px = self.meters_to_pixels(body.position.x)
        y_px = self.meters_to_pixels(body.position.y)
        vx_px = self.meters_to_pixels(body.linearVelocity.x)
        vy_px = self.meters_to_pixels(body.linearVelocity.y)

        entity.pos = pygame.Vector2(x_px, y_px)
        entity.vel = pygame.Vector2(vx_px, vy_px)
        entity.rect.center = (int(x_px), int(y_px))
        entity.angle = -float(body.angle) * 57.29577951308232
