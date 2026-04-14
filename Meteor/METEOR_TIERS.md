# Kolmiosainen Meteorijärjestelmä (Meteor Tiers)

## Yleiskatsaus

Pelissä on nyt kolmiosainen meteorijärjestelmä, jossa meteorit hajoavat pienempiin osiin ammuksella:

| Taso | Nimi | Koko | Kuva | Vauriot | Fragmentaatio |
|------|------|------|------|---------|---------------|
| 1 (100%) | **MainMeteorite** | 300×300px | Meteor_01.png | 2 HP | Hajoaa 4x Meteor (50%) |
| 2 (50%) | **Meteor** | 150×150px | Meteor_05.png | 1 HP | Hajoaa 2x SmallMeteorite (25%) |
| 3 (25%) | **SmallMeteorite** | 75×75px | Meteor_10.png | 1 HP | Ei hajoa |

## Meteorin Luokat

### MainMeteorite - Isoin meteorii (100%)

**Ominaisuudet:**
- Koko: ~300×300 pikseliä
- Kuva: `Space-Shooter_objects/PNG/Meteors/Meteor_01.png`
- Vauriot pelaajalle: 2 health
- Health: 1 (kestää 1 ammusta)
- Fragmentaatio: Hajoaa 4 pienempään Medium-meteoriin (50%)

**Käyttö:**
```python
from Meteor.meteor import MainMeteorite

main_meteor = MainMeteorite(
    x=800,
    y=400,
    bounds=(1600, 800),
    speed=100,
    velocity=(50, 50)  # Vektori tai None
)
game.meteors.append(main_meteor)
```

### Meteor - Keskikokoinen meteorii (50%)

**Ominaisuudet:**
- Koko: ~150×150 pikseliä
- Kuva: `Space-Shooter_objects/PNG/Meteors/Meteor_05.png`
- Vauriot pelaajalle: 1 health
- Health: 1 (kestää 1 ammusta)
- Fragmentaatio: Hajoaa 2 pienempään Small-meteoriin (25%)

**Käyttö:**
```python
from Meteor.meteor import Meteor

meteor = Meteor(
    x=800,
    y=400,
    bounds=(1600, 800),
    speed=80,
    velocity=(40, 40),
    size_scale=0.5  # Tämä on oletusarvo
)
game.meteors.append(meteor)
```

### SmallMeteorite - Pienin meteorii (25%)

**Ominaisuudet:**
- Koko: ~75×75 pikseliä
- Kuva: `Space-Shooter_objects/PNG/Meteors/Meteor_10.png`
- Vauriot pelaajalle: 1 health
- Health: 1 (kestää 1 ammusta)
- Fragmentaatio: **Ei hajoa** - katoaa kun ammuttu

**Käyttö:**
```python
from Meteor.meteor import SmallMeteorite

small_meteor = SmallMeteorite(
    x=800,
    y=400,
    bounds=(1600, 800),
    speed=80,
    velocity=(30, 30)
)
game.meteors.append(small_meteor)
```

## Fragmentaatiologiikka

### Kuinka fragmentaatio toimii

1. **Ammuksen törmäys meteoriin:**
   - Ammuksen colliderect() tarkistaa, onko se osuneet meteoriin
   - Ammus poistetaan

2. **Vaurioiden käsittely:**
   - Meteorin `health` vähenee 1:llä
   - Jos `health <= 0`:
     - Meteorin `get_fragments()` kutsutaan
     - Fragmentit lisätään `self.meteors` listalle
     - Meteorin `dead = True` asetetaan

3. **Fragmenttien sijoittelu:**
   ```
   MainMeteorite (100%)
   ├── Meteor 1 (50%)
   ├── Meteor 2 (50%)
   ├── Meteor 3 (50%)
   └── Meteor 4 (50%)
       
       Meteor (50%)
       ├── SmallMeteorite 1 (25%)
       └── SmallMeteorite 2 (25%)
   ```

## Spawn-funktiot

### spawn_moving_meteor() - Klusterispawn

Spawnaa liikkuvaa meteoreja klusterissa (iso + 2-4 pienempää):

```python
from Meteor.meteor_helpers import spawn_moving_meteor

# Spawn MainMeteorite + pieni klusterispawn
spawn_moving_meteor(game, speed=100, use_main=True)

# Spawn Meteor (50%) + pieni klusterispawn
spawn_moving_meteor(game, speed=100, use_main=False)
```

**Parametrit:**
- `game`: Game-instanssi
- `speed`: Nopeus pixels/sekunti (oletus 80)
- `use_main`: Jos True, käytä MainMeteorite; muuten Meteor (50%)

### spawn_meteor() - Yksittäinen meteorii

```python
from Meteor.meteor_helpers import spawn_meteor

# Spawn MainMeteorite
spawn_meteor(game, x=800, y=400, meteor_type="main")

# Spawn Meteor (50%)
spawn_meteor(game, x=800, y=400, meteor_type="medium")

# Spawn SmallMeteorite
spawn_meteor(game, x=800, y=400, meteor_type="small")
```

**Parametrit:**
- `game`: Game-instanssi
- `x`, `y`: Sijainti
- `meteor_type`: "main", "medium" tai "small"

## Esimerkkitaso - Meteorispawni

```python
from Meteor.meteor_helpers import spawn_moving_meteor

def update_level(game, dt):
    # Spawnaa uusi meteoriklusterispawn alle 3 sekuntia
    if not hasattr(game, 'meteor_spawn_timer'):
        game.meteor_spawn_timer = 0
    
    game.meteor_spawn_timer += dt
    if game.meteor_spawn_timer > 3000:  # 3 sekuntia
        spawn_moving_meteor(game, speed=120, use_main=True)
        game.meteor_spawn_timer = 0
```

## Ammuksien Törmäystarkistus

RocketGame.py:n update()-metodissa käsitellään ammuksien törmäys meteoreihin:

```python
# Legacy meteor update path (non-test levels)
if self.hazard_system is None:
    for meteor in list(self.meteors):
        meteor.update(self.dt)
        if getattr(meteor, 'dead', False):
            self.meteors.remove(meteor)

# Ammuksien käsittely - meteorit
for meteor in list(self.meteors):
    for bullet in list(self.player.weapons.bullets):
        if bullet.rect.colliderect(meteor.rect):
            if bullet in self.player.weapons.bullets:
                self.player.weapons.bullets.remove(bullet)
            
            # Handle meteor fragmentation if meteor has health
            if hasattr(meteor, 'health') and hasattr(meteor, 'get_fragments'):
                meteor.health -= 1
                if meteor.health <= 0:
                    # Meteor destroyed - spawn fragments
                    fragments = meteor.get_fragments()
                    self.meteors.extend(fragments)
                    meteor.dead = True
            
            break

# Remove dead meteors
self.meteors = [m for m in self.meteors if not m.dead]
```

## Attribuutit ja Metodit

### Kaikilla meteoriluokilla:

```python
meteor.pos              # pygame.Vector2 - sijainti
meteor.vel              # pygame.Vector2 - nopeus
meteor.rect             # pygame.Rect - piirtöalue
meteor.health          # int - terveys (1 oletuksena)
meteor.max_health      # int - max terveys
meteor.damage_to_player # int - vauriot pelaajalle
meteor.meteor_type     # str - "main", "medium", "small"
meteor.dead            # bool - onko kuollut

# Metodit:
meteor.update(dt)       # Päivitä sijainti (dt millisekuntia)
meteor.draw(surface, camera_x, camera_y)  # Piirrä meteorii
meteor.get_fragments()  # Palauta fragmentit listana
```

## Testaus

Testaa järjestelmää:

```python
# 1. Luo MainMeteorite
main = MainMeteorite(800, 400, bounds=(1600, 800))

# 2. Ammukset osuvat siihen
main.health = 0  # Simuloi ammuksen osumaa
fragments = main.get_fragments()  # Pitäisi palauttaa 4x Meteor

# 3. Tarkista fragmentit
assert len(fragments) == 4
for frag in fragments:
    assert frag.meteor_type == "medium"
    assert frag.health == 1
    assert frag.damage_to_player == 1
```

## Yhteensopivuus Hazard_systemin kanssa

Jos käytät `hazard_system` (test-leveleilla), sillä on oma `MeteorHazard`-luokka:
- Hazard_system käyttää 3-tasoista meteorijärjestelmää omilla kuvilla
- MainMeteorite, Meteor, SmallMeteorite ovat erilliset ja käytetään `spawn_moving_meteor()`:lla

Niiden ei tarvitse olla yhteensopivia, mutta ne voivat olla rinnakkain.
