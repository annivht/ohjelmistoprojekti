"""
Module: RocketGame.py
Dependencies: pygame, os, random, SpriteSettings, PLAYER_LUOKAT.Player (Player), EnemyAI (StraightEnemy, CircleEnemy), boss_enemy (BossEnemy), Points
Provides: main game loop, loads sprites and spawns enemies/boss, handles collisions and draws
Uses: EnemyHelpers for specific explosion spawn when needed
"""

import sys
import os
import pygame
import random
from Enemies.enemy import StraightEnemy, CircleEnemy, DownEnemy, UpEnemy
from boss_enemy import BossEnemy
from points import Points
sys.path.append(os.path.dirname(__file__))
from Player import Player
from player2 import Player2
from Valikot.NextLevel import NextLevel
from Valikot.gameOver import GameOverScreen
from SpriteSettings import SpriteSettings
from explosion import ExplosionManager
from collisions import SpatialHash, apply_impact, separate, _get_pos, get_collision_radius
from ui import init_enemy_health_bars
import planets

from GameStateManager import GameStateManager
# Näytön koko
X, Y = 1600, 800
HEALTH_ICON_SIZE = (600, 200)
HEALTH_ICON_MARGIN = 16
max_w = max(1, X - 2 * HEALTH_ICON_MARGIN)
max_h = max(1, Y - 2 * HEALTH_ICON_MARGIN)
scale = min(max_w / HEALTH_ICON_SIZE[0], max_h / HEALTH_ICON_SIZE[1], 1.0)
HEALTH_ICON_SCALE_SIZE = (max(1, int(HEALTH_ICON_SIZE[0]*scale)), max(1, int(HEALTH_ICON_SIZE[1]*scale)))
HEALTH_ICON_POS = (X - HEALTH_ICON_SCALE_SIZE[0] - HEALTH_ICON_MARGIN, HEALTH_ICON_MARGIN)

# Hitbox-koko per tyyppi
HITBOX_SIZE_PLAYER = (64, 64)
HITBOX_SIZE_ENEMY = (48, 48)
HITBOX_SIZE_BOSS = (140, 140)


def apply_hitbox(obj, size=None):
    """Asettaa objektin hitboxin ja collision_radiusin"""
    if size is None:
        return
    c = obj.rect.center
    w, h = int(size[0]), int(size[1])
    obj.rect.size = (w, h)
    obj.rect.center = c
    if hasattr(obj, 'pos'):
        obj.pos = pygame.Vector2(obj.rect.center)
    try:
        obj.collision_radius = max(8, int(max(obj.rect.width, obj.rect.height)*0.45))
    except Exception:
        pass


class Game:
    """Modulaarinen RocketGame-luokka, ohjattavissa PlayState kautta"""

    def __init__(self, screen):
        self.screen = screen
        self.dt = 0
        self.camera_x = 0
        self.camera_y = 0
        self.running = True
        self.pause = False

        # Peliobjektit
        self.player = None
        self.enemies = []
        self.enemy_bullets = []
        self.muzzles = []
        self.boss = None
        self.current_wave = 1
        self.MAX_WAVE = 4
        self.wave_cleared = False
        self.boss_clear_menu_delay_remaining = None
        self.lives = 3
        self.enemy_hit_cooldown = 0
        self.enemy_hit_cooldown_duration = 1000
        self.pistejarjestelma = None

        # Pygame-resurssit
        self.clock = pygame.time.Clock()
        self.explosion_manager = ExplosionManager()
        self.spatial_hash = SpatialHash()
        self.collisions = set()
        self.DEBUG_DRAW_COLLISIONS = True
        self.USE_SPATIAL_COLLISIONS = True

        # Lataa tausta ja planeetat
        self._load_assets()

        # Alusta pelaaja ja ensimmäinen wave
        self.init_game_objects()

    def _load_assets(self):
        """Lataa tausta, vihollisten kuvat ja planeetat"""
        base_path = os.path.dirname(__file__)
        self.tausta = pygame.image.load(os.path.join(base_path,'images','taustat','avaruus.png')).convert()
        self.tausta = pygame.transform.scale(self.tausta, (X, Y))
        self.tausta_leveys, self.tausta_korkeus = self.tausta.get_width(), self.tausta.get_height()

        # Lataa vihollisten kuvat
        viholliset_path = os.path.join(base_path, "images", "viholliset")
        self.enemy_imgs = [
            pygame.transform.scale(
                pygame.image.load(os.path.join(viholliset_path, f)).convert_alpha(),
                (64, 64)
            )
            for f in sorted([fn for fn in os.listdir(viholliset_path) if fn.lower().endswith(".png")],
                            key=lambda name: int(os.path.splitext(name)[0]))
        ]

        # SpriteSettings vihollisille
        self.ss = SpriteSettings(base_path=os.path.join(base_path, 'enemy-sprite'))
        self.ss.load_all()

        # Boss kuva
        self.boss_image = pygame.transform.scale(
            pygame.image.load(os.path.join(viholliset_path, "12.png")).convert_alpha(),
            (320, 320)
        )

        # Planeetat
        self.planeetat = [
            pygame.transform.scale(pygame.image.load(f"images/planeetat/slice{i}.png"), (100,100))
            for i in range(2,11)
        ]
        self.planeetta_paikat = [
            (random.randint(0, max(0,self.tausta_leveys-300)),
             random.randint(0, max(0,self.tausta_korkeus-300)))
            for _ in range(len(self.planeetat))
        ]

    def init_game_objects(self):
        """Alusta pelaaja, pistejärjestelmä ja ensimmäinen wave"""
        self.pistejarjestelma = Points()

        player_ship = 'FIGHTER'
        player_start_x = self.tausta_leveys // 2
        player_start_y = self.tausta_korkeus // 2
        player_scale_factor = 1

        try:
            self.player = Player2(player_ship, player_scale_factor, player_start_x, player_start_y, max_health=5)
        except Exception:
            self.player = Player(player_scale_factor, [], player_start_x, player_start_y, boost_frames=[], max_health=5)

        apply_hitbox(self.player, HITBOX_SIZE_PLAYER)
        self.spawn_wave(self.current_wave)

    def reset_game(self):
        """Resettaa pelin tilan ja pelaajan"""
        self.current_wave = 1
        self.wave_cleared = False
        self.boss_clear_menu_delay_remaining = None
        self.enemies.clear()
        self.enemy_bullets.clear()
        self.muzzles.clear()
        self.collisions.clear()
        self.player.health = getattr(self.player, 'max_health', 5)
        self.lives = self.player.health
        self.spawn_wave(self.current_wave)
        self.pistejarjestelma = Points()
        pygame.event.clear()

    def spawn_wave(self, wave_num):
        """Spawnaa viholliset wave-numeroon perustuen"""
        self.enemies.clear()
        if wave_num == 1:
            e1 = StraightEnemy(self.enemy_imgs[0], 200, 200, speed=220)
            e2 = CircleEnemy(self.enemy_imgs[1], self.tausta_leveys//2+300, self.tausta_korkeus//2, radius=180, angular_speed=2.2)
            for e in [e1, e2]:
                apply_hitbox(e, HITBOX_SIZE_ENEMY)
                self.enemies.append(e)
        elif wave_num == 4:
            self.boss = BossEnemy(self.boss_image, pygame.Rect(0,0,self.tausta_leveys,self.tausta_korkeus),
                                   hp=12, enter_speed=280, move_speed=320, hitbox_size=HITBOX_SIZE_BOSS, hitbox_offset=(0,0))
            apply_hitbox(self.boss, HITBOX_SIZE_BOSS)
            self.enemies.append(self.boss)

        # Muut wavet voidaan lisätä samalla logiikalla

    def update(self, events):
        """Päivitä pelilogiikka: pelaaja, viholliset, ammukset, collisionit jne."""
        self.dt = self.clock.tick(60)

        # Päivitä planeetat ja pelaaja
        planets.update_planet(self.dt)
        self.player.update(self.dt)
        self.player.move(0,0,self.tausta_leveys,self.tausta_korkeus)

        # Kamera pelaajan ympärillä
        self.camera_x = max(0, min(self.player.rect.centerx - X//2, self.tausta_leveys - X))
        self.camera_y = max(0, min(self.player.rect.centery - Y//2, self.tausta_korkeus - Y))

        # Päivitä viholliset
        for e in self.enemies:
            e.update(self.dt, self.player, pygame.Rect(0,0,self.tausta_leveys,self.tausta_korkeus))
            if isinstance(e, BossEnemy):
                e.maybe_shoot(self.dt, {'bullets': self.enemy_bullets, 'muzzles': self.muzzles}, player=self.player)
            else:
                e.maybe_shoot(self.dt, {'bullets': self.enemy_bullets, 'muzzles': self.muzzles})

        # Ammukset
        for bullet in list(self.player.weapons.bullets):
            for enemy in list(self.enemies):
                if bullet.rect.colliderect(enemy.rect):
                    impact_pos = bullet.rect.center
                    self.player.weapons.bullets.remove(bullet)
                    if isinstance(enemy, BossEnemy):
                        died = enemy.take_hit(1)
                        if died:
                            self.explosion_manager.spawn_boss(enemy.rect.center, fps=24)
                            self.enemies.remove(enemy)
                            self.pistejarjestelma.lisaa_piste(5)
                        else:
                            self.explosion_manager.spawn_enemy(impact_pos, fps=24)
                    else:
                        self.explosion_manager.spawn_enemy(impact_pos, fps=24)
                        self.enemies.remove(enemy)
                        self.pistejarjestelma.lisaa_piste(1)
                    break

        for b in list(self.enemy_bullets):
            b.update(self.dt, pygame.Rect(0,0,self.tausta_leveys,self.tausta_korkeus))
            if getattr(b,'dead',False):
                self.enemy_bullets.remove(b)
            elif getattr(b,'state','')=='flight' and b.rect.colliderect(self.player.rect):
                b.explode()
                self.enemy_bullets.remove(b)
                self.player.health = max(0, self.player.health-1)
                self.lives = self.player.health

        # Räjähdykset
        self.explosion_manager.update(self.dt)

    def draw(self, target_screen):
        """Piirrä kaikki peliobjektit annettuun ruutuun"""
        self.screen = target_screen
        self.screen.blit(self.tausta, (0,0), area=(self.camera_x, self.camera_y, X, Y))

        for kuva, (x, y) in zip(self.planeetat, self.planeetta_paikat):
            self.screen.blit(kuva, (x - self.camera_x, y - self.camera_y))

        for e in self.enemies:
            e.draw(self.screen, self.camera_x, self.camera_y)

        for b in self.enemy_bullets:
            b.draw(self.screen, self.camera_x, self.camera_y)

        for m in self.muzzles:
            m.draw(self.screen, self.camera_x, self.camera_y)

        self.player.draw(self.screen, self.camera_x, self.camera_y)
        self.explosion_manager.draw(self.screen, self.camera_x, self.camera_y)

        self.pistejarjestelma.show_score(10,10, pygame.font.SysFont('Arial',24), self.screen)


# Compatibility bridge for old function-style callers.
_active_game = None


def init(screen):
    """Initialize a single active Game instance for legacy callers."""
    global _active_game
    _active_game = Game(screen)
    return _active_game


def update(events):
    """Update active Game instance if initialized."""
    if _active_game is not None:
        _active_game.update(events)


def draw(screen):
    """Draw active Game instance if initialized."""
    if _active_game is not None:
        _active_game.draw(screen)


def is_running():
    """Return whether active Game instance is running."""
    return _active_game is not None and bool(_active_game.running)


def get_active_game():
    """Expose active game for code that still needs direct access."""
    return _active_game

"""

# Keep backward compatibility: running `py RocketGame.py` should now start
# through the new state system (main menu first) instead of this legacy loop.
if __name__ == "__main__":
    import main as state_entry

    state_entry.main()
    raise SystemExit

pygame.init()
Y = 800
X = 1600

# Health icon size (width, height) - change this to scale health HUD
HEALTH_ICON_SIZE = (600, 200)
# Margin from screen edges for HUD icons
HEALTH_ICON_MARGIN = 16

# Compute a safe icon size that won't run off the screen and preserve aspect
# (will be used when loading/scale images)
# Use window size `X,Y` and margin to limit maximum icon size
max_w = max(1, X - 2 * HEALTH_ICON_MARGIN)
max_h = max(1, Y - 2 * HEALTH_ICON_MARGIN)
scale_w = max_w / HEALTH_ICON_SIZE[0]
scale_h = max_h / HEALTH_ICON_SIZE[1]
scale = min(scale_w, scale_h, 1.0)
HEALTH_ICON_SCALE_SIZE = (max(1, int(HEALTH_ICON_SIZE[0] * scale)), max(1, int(HEALTH_ICON_SIZE[1] * scale)))

# HUD position for health icon (top-right corner with margin)
HEALTH_ICON_POS = (X - HEALTH_ICON_SCALE_SIZE[0] - HEALTH_ICON_MARGIN, HEALTH_ICON_MARGIN)

screen = pygame.display.set_mode((X,Y))

# Hitbox override per entity type: set to (W, H) to force rectangle size,
# or None to use the sprite's intrinsic rect size. These three settings
# allow independent tuning for player, generic enemies and boss.
# Examples:
#   HITBOX_SIZE_PLAYER = (48, 48)
#   HITBOX_SIZE_ENEMY  = (56, 56)
#   HITBOX_SIZE_BOSS   = (240, 240)
HITBOX_SIZE_PLAYER = (64, 64)
HITBOX_SIZE_ENEMY = (48, 48)
HITBOX_SIZE_BOSS = (140, 140)


def apply_hitbox(obj, size=None):
    if size is None:
        return
    try:
        c = obj.rect.center
        w, h = int(size[0]), int(size[1])
        obj.rect.size = (w, h)
        obj.rect.center = c
        if hasattr(obj, 'pos'):
            obj.pos = pygame.Vector2(obj.rect.center)
        try:
            # keep compatibility with Enemy defaults (MIN_COLLISION_RADIUS etc.)
            obj.collision_radius = max(8, int(max(obj.rect.width, obj.rect.height) * 0.45))
        except Exception:
            pass
    except Exception:
        pass

# load, convert and scale background to window size
tausta = pygame.image.load(os.path.join(os.path.dirname(__file__),'images','taustat','avaruus.png')).convert()
tausta = pygame.transform.scale(tausta, (X, Y))

# Lataa planeetat ja arvo niiden paikat ison taustan mukaan
planeetat = [
    pygame.transform.scale(pygame.image.load("images/planeetat/slice2.png"), (100, 100)),
    pygame.transform.scale(pygame.image.load("images/planeetat/slice3.png"), (100, 100)),
    pygame.transform.scale(pygame.image.load("images/planeetat/slice4.png"), (100, 100)),
    pygame.transform.scale(pygame.image.load("images/planeetat/slice5.png"), (100, 100)),
    pygame.transform.scale(pygame.image.load("images/planeetat/slice6.png"), (100, 100)),
    pygame.transform.scale(pygame.image.load("images/planeetat/slice7.png"), (100, 100)),
    pygame.transform.scale(pygame.image.load("images/planeetat/slice8.png"), (100, 100)),
    pygame.transform.scale(pygame.image.load("images/planeetat/slice9.png"), (100, 100)),
    pygame.transform.scale(pygame.image.load("images/planeetat/slice10.png"), (100, 100)),
]

tausta_leveys, tausta_korkeus = tausta.get_width(), tausta.get_height()

#  Viholliset: kuvat ja oliot 
viholliset_path = os.path.join(os.path.dirname(__file__), "images", "viholliset")

enemy_imgs = [
    pygame.transform.scale(
        pygame.image.load(os.path.join(viholliset_path, f)).convert_alpha(),
        (64, 64)
    )
    for f in sorted(
        [fn for fn in os.listdir(viholliset_path) if fn.lower().endswith(".png")],
        key=lambda name: int(os.path.splitext(name)[0])  # "1.png" -> 1
    )
]

# Load sprite settings for optional enemy visuals
ss = SpriteSettings(base_path=os.path.join(os.path.dirname(__file__), 'enemy-sprite'))
ss.load_all()
# BOSS kuva
boss_image = pygame.transform.scale(
    pygame.image.load(os.path.join(viholliset_path, "12.png")).convert_alpha(),
    (320, 320)  # iso boss
)


world_rect = pygame.Rect(0, 0, tausta_leveys, tausta_korkeus)

# bossin räjädysanimaation frames (moved to ExplosionManager)
# create a manager and load default frames from the standard folder
explosion_manager = ExplosionManager()
# Populate type-specific frames without try/except by checking folders explicitly
base_expl_dir = os.path.join(os.path.dirname(__file__), 'enemy-sprite', 'PNG_Parts&Spriter_Animation', 'Explosions')
boss_folder = os.path.join(base_expl_dir, 'Explosion1')
if os.path.isdir(boss_folder):
    boss_frames = ExplosionManager.load_frames(folder=boss_folder, size=(300, 300))
    if boss_frames:
        explosion_manager.set_frames_for('boss', boss_frames)

# enemy uses the same Explosion1 frames but smaller
if os.path.isdir(boss_folder):
    enemy_frames = ExplosionManager.load_frames(folder=boss_folder, size=(80, 80))
    if enemy_frames:
        explosion_manager.set_frames_for('enemy', enemy_frames)

# player frames: search under alukset/alus/*/Destroyed for the first valid folder
player_folder = None
alukset_alus = os.path.join(os.path.dirname(__file__), 'alukset', 'alus')
if os.path.isdir(alukset_alus):
    for candidate in sorted(os.listdir(alukset_alus)):
        cand = os.path.join(alukset_alus, candidate, 'Destroyed')
        if os.path.isdir(cand):
            player_folder = cand
            break

if player_folder:
    player_frames = ExplosionManager.load_frames(folder=player_folder, size=(220, 220), pattern=r"(.*)\\.png")
    if player_frames:
        explosion_manager.set_frames_for('player', player_frames)

# Ensure there is a generic fallback frame list if nothing type-specific was loaded
if not explosion_manager.frames and os.path.isdir(boss_folder):
    generic = ExplosionManager.load_frames(folder=boss_folder, size=(200, 200))
    if generic:
        explosion_manager.set_frames(generic)

# Report current ammo presets and whether player has shot frames/ammo images
try:
    from Ammus import Ammus
    preset_summary = {k: {kk: v for kk, v in Ammus.PRESETS[k].items()} for k in Ammus.PRESETS}
    print('Ammus presets:', preset_summary)
except Exception:
    pass

# Collision and UI helpers moved to modules for modularity
USE_SPATIAL_COLLISIONS = True


# Debug toggle: draw collision rects and collision radii on screen.
# Set to False to disable visual debug overlays.
DEBUG_DRAW_COLLISIONS = True

# Instantiate spatial hash and collision state
spatial_hash = SpatialHash()
collisions = set()

# Wave system - Poista nämä myöhemmin !!!!! 
enemies = []
current_wave = 1
MAX_WAVE = 4
wave_cleared = False
BOSS_CLEAR_MENU_DELAY_MS = 1800
boss_clear_menu_delay_remaining = None
# Poista nämä myöhemmin !!!!!

def clear_round_state():
    enemies.clear()
    enemy_bullets.clear()
    muzzles.clear()
    collisions.clear()
    try:
        player.weapons.bullets.clear()
    except Exception:
        pass

# pelin reset
def reset_game():
    global current_wave, wave_cleared, lives, enemy_hit_cooldown,pistejarjestelma, boss_clear_menu_delay_remaining

    # wave reset
    current_wave = 1
    wave_cleared = False
    boss_clear_menu_delay_remaining = None

    # clear enemies + enemy bullets + muzzle effects+ collisions
    clear_round_state()
    #resetplayer health + lives
    
    player.health = int(getattr(player, "max_health", 5))
    lives = player.health
   

    # reset player
 
    player.pos = pygame.Vector2(player_start_x, player_start_y)
    player.rect.center = (int(player.pos.x), int(player.pos.y))
    player.vel = pygame.Vector2(0, 0)
    
    enemy_hit_cooldown = 0

    # spawn wave 1 properly
    spawn_wave(current_wave)
    pygame.event.clear()

    # reset score 
    pistejarjestelma = Points() 

#“RESTART = aloita sama taso alusta”
def restart_current_wave():
    global enemy_hit_cooldown, lives, collisions

    # tyhjennä kaikki kesken jääneet asiat
    clear_round_state()

    # reset player
    player.health = int(getattr(player, "max_health", 5))
    lives = player.health

    try:
        player.pos = pygame.Vector2(player_start_x, player_start_y)
        player.rect.center = (int(player.pos.x), int(player.pos.y))
        player.vel = pygame.Vector2(0, 0)
    except Exception:
        player.rect.center = (player_start_x, player_start_y)

    enemy_hit_cooldown = 0

    # tärkein: käynnistä NYKYINEN wave alusta
    spawn_wave(current_wave)

    pygame.event.clear()

def spawn_inside_edge(edge, inset=80):
    # inset = kuinka paljon sisällä reunasta
    if edge == "left":
        return inset, random.randint(inset, tausta_korkeus - inset)
    if edge == "right":
        return tausta_leveys - inset, random.randint(inset, tausta_korkeus - inset)
    if edge == "top":
        return random.randint(inset, tausta_leveys - inset), inset
    if edge == "bottom":
        return random.randint(inset, tausta_leveys - inset), tausta_korkeus - inset
    return random.randint(inset, tausta_leveys - inset), random.randint(inset, tausta_korkeus - inset)

def spawn_wave(wave_num):
    global enemies
    enemies.clear()
    
    if wave_num == 1:
        # Wave 1: 2 enemies (original)
        # Prefer ship frames from SpriteSettings if available, else fallback to the old folder images
        ship_frames = ss.ship_frames if hasattr(ss, 'ship_frames') and ss.ship_frames else None
        exhaust_turbo = ss.exhaust_turbo if hasattr(ss, 'exhaust_turbo') else []
        exhaust_normal = ss.exhaust_normal if hasattr(ss, 'exhaust_normal') else []
        shot_frames = ss.shot_frames if hasattr(ss, 'shot_frames') else []

        img0 = ship_frames[0] if ship_frames and len(ship_frames) > 0 else enemy_imgs[0]
        img1 = ship_frames[1] if ship_frames and len(ship_frames) > 1 else enemy_imgs[1]

        e1 = StraightEnemy(img0, 200, 200, speed=220)
        e1.exhaust_turbo = exhaust_turbo
        e1.exhaust_normal = exhaust_normal
        e1.shots = shot_frames
        # explicit collision radius (use sprite size, not any orbital `radius` field)
        try:
            e1.collision_radius = max(8, int(max(e1.rect.width, e1.rect.height) * 0.45))
        except Exception:
            e1.collision_radius = 16
        enemies.append(e1)
        apply_hitbox(e1, HITBOX_SIZE_ENEMY)

        e2 = CircleEnemy(img1, tausta_leveys // 2 + 300, tausta_korkeus // 2, radius=180, angular_speed=2.2)
        e2.exhaust_turbo = exhaust_turbo
        e2.exhaust_normal = exhaust_normal
        e2.shots = shot_frames
        try:
            e2.collision_radius = max(8, int(max(e2.rect.width, e2.rect.height) * 0.45))
        except Exception:
            e2.collision_radius = 16
        enemies.append(e2)
        apply_hitbox(e2, HITBOX_SIZE_ENEMY)
    
    elif wave_num == 2:
        edges = ["right", "top", "left"]
        for i, edge in enumerate(edges):
            x, y = spawn_inside_edge(edge, inset=80)
            e = StraightEnemy(enemy_imgs[i % len(enemy_imgs)], x, y, speed=220)

            # anna satunnainen lähtösuunta ettei se jää sahaamaan reunaa
            if hasattr(e, "vel"):
                v = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
                if v.length_squared() == 0:
                    v = pygame.Vector2(1, 0)
                e.vel = v.normalize() * 220

            try:
                e.collision_radius = max(8, int(max(e.rect.width, e.rect.height) * 0.45))
            except Exception:
                e.collision_radius = 16
            enemies.append(e)
            apply_hitbox(e, HITBOX_SIZE_ENEMY)
            apply_hitbox(e, HITBOX_SIZE_ENEMY)
    
    elif wave_num == 3:
        # Wave 3: 5 enemies - 3 moving from top to bottom, 2 moving from bottom to top
        spacing = tausta_leveys // 6  # 5 enemies with even spacing
        
        # 3 enemies moving down
        for i in range(3):
            x = spacing * (i + 1)
            y = 30
            e = DownEnemy(enemy_imgs[i % len(enemy_imgs)], x, y, speed=250)
            try:
                e.collision_radius = max(8, int(max(e.rect.width, e.rect.height) * 0.45))
            except Exception:
                e.collision_radius = 16
            enemies.append(e)
            apply_hitbox(e, HITBOX_SIZE_ENEMY)
        
        # 2 enemies moving up
        for i in range(2):
            x = spacing * (i + 3.5)
            y = tausta_korkeus - 30
            e = UpEnemy(enemy_imgs[(i + 3) % len(enemy_imgs)], x, y, speed=250)
            try:
                e.collision_radius = max(8, int(max(e.rect.width, e.rect.height) * 0.45))
            except Exception:
                e.collision_radius = 16
            enemies.append(e)
            apply_hitbox(e, HITBOX_SIZE_ENEMY)
    
    elif wave_num == 4:
        # Wave 4: Boss enemy
        boss = BossEnemy(
            boss_image,
            world_rect,
            hp=12,
            enter_speed=280,
            move_speed=320,
            hitbox_size=HITBOX_SIZE_BOSS,
            hitbox_offset=(0, 0),
        )
        try:
            boss.collision_radius = max(8, int(max(boss.rect.width, boss.rect.height) * 0.45))
        except Exception:
            boss.collision_radius = 64
        enemies.append(boss)
        apply_hitbox(boss, HITBOX_SIZE_BOSS)

# Spawn the first wave
enemy_bullets = []
muzzles = []
spawn_wave(current_wave)

def force_unstick(a, b, eps=2):
    pa = pygame.Vector2(a.rect.center)
    pb = pygame.Vector2(b.rect.center)
    d = pb - pa

    if d.length_squared() == 0:
        d = pygame.Vector2(1, 0)

    n = d.normalize()

    a.rect.centerx -= int(n.x * eps)
    a.rect.centery -= int(n.y * eps)
    b.rect.centerx += int(n.x * eps)
    b.rect.centery += int(n.y * eps)

    # jos enemy käyttää pos-vektoria, synkkaa se
    if hasattr(a, "pos"):
        a.pos = pygame.Vector2(a.rect.center)
    if hasattr(b, "pos"):
        b.pos = pygame.Vector2(b.rect.center)


planeetta_paikat = []
for _ in range(len(planeetat)):
    x = random.randint(0, max(0, tausta_leveys - 300))
    y = random.randint(0, max(0, tausta_korkeus - 300))
    planeetta_paikat.append((x, y))

# Initialize planets helper (loads sprite and rotation state)
try:
    # Select one large HD planet randomly from images/hd-planet and load it into planets module
    hd_dir = os.path.join(os.path.dirname(__file__), 'images', 'hd-planet')
    planet_height = max(800, int(Y * 1.4))
    if os.path.isdir(hd_dir):
        files = [f for f in os.listdir(hd_dir) if f.lower().endswith('.png')]
        if files:
            choice = random.choice(files)
            path = os.path.join(hd_dir, choice)
            try:
                surf = pygame.image.load(path).convert_alpha()
                # crop transparent padding so rotation pivots around the visible planet
                try:
                    bbox = surf.get_bounding_rect()
                    if bbox.width and bbox.height:
                        surf = surf.subsurface(bbox).copy()
                except Exception:
                    pass
                planets._sprite_orig = surf.copy()
                # scale base sprite to requested height
                if surf.get_height() != planet_height:
                    pw = max(1, int(surf.get_width() * (planet_height / surf.get_height())))
                    planets._sprite_base = pygame.transform.smoothscale(surf, (pw, planet_height))
                else:
                    planets._sprite_base = surf
                # set a modest rotation speed
                try:
                    planets._angle = 0.0
                    planets._rot_speed = 12.0
                except Exception:
                    pass
            except Exception:
                # fallback to module initializer
                try:
                    planets.init_planet(os.path.dirname(__file__), filename=None, height=320, rot_speed_deg=36.0)
                except Exception:
                    pass
        else:
            planets.init_planet(os.path.dirname(__file__), filename=None, height=320, rot_speed_deg=36.0)
    else:
        planets.init_planet(os.path.dirname(__file__), filename=None, height=320, rot_speed_deg=36.0)
except Exception:
    pass

# Initialize enemy health bar images in UI module (modularized)
try:
    init_enemy_health_bars(os.path.dirname(__file__))
except Exception:
    try:
        init_enemy_health_bars()
    except Exception:
        pass



# -----------------------------
# Pelaajan (Player) lataus ja asetukset
# - Player-olio maailman keskelle
# -----------------------------


# Luodaan pistelaskuriolio.
pistejarjestelma = Points()

# Luo pelaaja maailman keskelle. Valitse aluksen nimi tähän (esim. 'Bomber', 'FIGHTER')
player_ship = os.environ.get('PLAYER_SHIP', 'FIGHTER')
player_start_x = tausta_leveys // 2
player_start_y = tausta_korkeus // 2
player_scale_factor = 1  # Skaalaa pelaajan sprite.

# Käytä uutta `Player2`-luokkaa joka lataa spritet dynaamisesti
try:
    player = Player2(player_ship, player_scale_factor, player_start_x, player_start_y, max_health=5)
    apply_hitbox(player, HITBOX_SIZE_PLAYER)
except Exception as e:
    # Tulostetaan poikkeus syyksi, jotta tiedetään miksi Player2 epäonnistui
    import traceback
    traceback.print_exc()
    print('Player2 init failed, falling back to legacy Player:', e)
    # varmistus: paluu takaisin vanhaan Player-luokkaan jos jokin menee pieleen
    # Korvataan aiempi kovakoodattu lataus tyhjillä frame-listoilla
    frames = []
    boost_frames = []
    player = Player(player_scale_factor, frames, player_start_x, player_start_y, boost_frames=boost_frames, max_health=5)
    apply_hitbox(player, HITBOX_SIZE_PLAYER)

# Debug: kerrotaan käytössä oleva pelaajaluokka ja skaala-arvot
try:
    print(f"Player instance: {type(player)}")
    print(f"player.scale_factor = {getattr(player, 'scale_factor', None)}")
    # jos pelaajalla on kuvaattribuutti, näytetään sen koko
    if getattr(player, 'image', None) is not None:
        print('player.image.get_size() =', player.image.get_size())
except Exception:
    pass

# Pelaajan elämät / health
lives = 3
enemy_hit_cooldown = 0
enemy_hit_cooldown_duration = 1000  # 1 sekunti (millisekuntia)

# Load health UI sprites (images/elementit/15.png .. 20.png)
health_imgs = {}
health_dir = os.path.join(os.path.dirname(__file__), 'images', 'elementit')
for h in range(0, 6):
    img_index = 15 + h
    path = os.path.join(health_dir, f"{img_index}.png")
    try:
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.scale(img, HEALTH_ICON_SCALE_SIZE)
        health_imgs[h] = img
    except Exception:
        health_imgs[h] = None

# Kello frameratea ja animaatiota varten
clock = pygame.time.Clock()

# Luodaan Game Over -näyttöolio.
game_over_screen = GameOverScreen(screen)

# Alusta kamera ennen silmukkaa
camera_x = 0
camera_y = 0
run = True
pause = False
ENABLE_LEGACY_LOOP = False

while ENABLE_LEGACY_LOOP and run:
    # Tapahtumien käsittely
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pause = True
    # rajoita framerate ja hae dt (millisekunteina)
    dt = clock.tick(60)
    planets.update_planet(dt)

    # Päivitä pelaaja (animaatio + näppäinliike)
    player.update(dt)
    # Varmista, että pelaaja pysyy taustan sisällä
    player.move(0, 0, tausta_leveys, tausta_korkeus)


    # Keskitetään kamera pelaajaan (kameran sijainti maailmassa)
    camera_x = player.rect.centerx - X // 2
    camera_y = player.rect.centery - Y // 2
    
    # Rajoita kamera taustan reunoihin
    camera_x = max(0, min(camera_x, tausta_leveys - X))
    camera_y = max(0, min(camera_y, tausta_korkeus - Y))

    # Piirrä tausta kameran kohdalta
    screen.blit(tausta, (0, 0), area=(camera_x, camera_y, X, Y))

    # Draw a large rotating decorative planet always visible (screen coords)
    try:
        # Draw a very large planet off to the right (mostly off-screen) so it appears huge
        big_h = max(800, int(Y * 1.4))
        center_x = X + (big_h // 4)
        center_y = Y // 2
        planets.draw_planet_screen(screen, center_x, center_y, height=big_h, gap=0)
    except Exception:
        pass

    # Piirrä planeetat kameran offsetilla
    for kuva, (x, y) in zip(planeetat, planeetta_paikat):
        screen.blit(kuva, (x - camera_x, y - camera_y))
        
    # Piirrä viholliset ja anna niiden ampua (pois yrittävät try/except:t)
    for e in enemies:
        e.update(dt, player, world_rect)
        # BossEnemy supports targeting player for homing missiles
        if isinstance(e, BossEnemy):
            e.maybe_shoot(dt, {'bullets': enemy_bullets, 'muzzles': muzzles}, player=player)
        else:
            e.maybe_shoot(dt, {'bullets': enemy_bullets, 'muzzles': muzzles})

    # Draw boss health bars using BossEnemy method (moved into class)
    bosses = [be for be in enemies if isinstance(be, BossEnemy)]
    for idx, e in enumerate(bosses):
        e.draw_health_bar(screen, idx)

    # Optional: handle enemy-enemy collisions using spatial hash
    if USE_SPATIAL_COLLISIONS and len(enemies) > 1:
        try:
            # rebuild spatial hash from current enemy list
            spatial_hash.items = set(enemies)
            spatial_hash.rebuild()

            prev_collisions = collisions
            collisions = set()

            for b in enemies:
                possible = spatial_hash.query(b.rect)
                for a in possible:
                    if a is b:
                        continue
                    # compute simple circle overlap test
                    pa = _get_pos(a)
                    pb = _get_pos(b)
                    minsep = (get_collision_radius(a) +
                             get_collision_radius(b))
                    if pa.distance_squared_to(pb) < (minsep * minsep):
                        # canonical pair ordering
                        pair = (a, b) if id(a) < id(b) else (b, a)
                        if pair not in prev_collisions:
                            apply_impact(*pair)
                        collisions.add(pair)

            # separate with a few iterations for stability
            for _ in range(12):   # vähän enemmän iteraatioita
                new_collisions = set()

                for (a, b) in collisions:
                    still_colliding = not separate(a, b)

                    if still_colliding:
                        force_unstick(a, b)   # <-- tämä estää liimautumisen
                        new_collisions.add((a, b))

                collisions = new_collisions

                if not collisions:
                    break
        except Exception:
            # fail safe: continue without spatial collisions
            collisions = set()

    # Tarkista osumat pelaajaammuksien ja vihollisten välillä
    for bullet in list(player.weapons.bullets):
        for enemy in list(enemies):
            if bullet.rect.colliderect(enemy.rect):

                # Muistetaan osumakohta: käytä ammusten rectin keskusta
                impact_pos = bullet.rect.center

                # Poista ammus
                if bullet in player.weapons.bullets:
                    player.weapons.bullets.remove(bullet)

                # Boss kestää useita osumia
                if isinstance(enemy, BossEnemy):
                    died = enemy.take_hit(1)
                    if died:
                        # Bossin tuhoutumisessa pidetään suurempi boss-animaatio keskustassa
                        if explosion_manager.frames_by_type.get('boss'):
                            explosion_manager.spawn_boss(enemy.rect.center, fps=24)
                        elif explosion_manager.frames:
                            explosion_manager.spawn(enemy.rect.center, fps=24)

                        enemies.remove(enemy)
                        pistejarjestelma.lisaa_piste(5)
                    else:
                        # Pieni osumatehoste spawnataan siihen kohtaan, mihin ammus osui
                        if explosion_manager.frames_by_type.get('enemy'):
                            explosion_manager.spawn_enemy(impact_pos, fps=24)
                        elif explosion_manager.frames:
                            explosion_manager.spawn(impact_pos, fps=24)
                else:
                    # Normaali vihollinen kuolee heti -> spawn enemy or generic explosion
                    # Spawnataan animaatio siihen kohtaan, mihin ammus osui (impact_pos)
                    if explosion_manager.frames_by_type.get('enemy'):
                        explosion_manager.spawn_enemy(impact_pos, fps=24)
                    elif explosion_manager.frames:
                        explosion_manager.spawn(impact_pos, fps=24)

                    enemies.remove(enemy)
                    pistejarjestelma.lisaa_piste(1)

                break  # Siirry seuraavaan ammukseen

    # Wave progression system
    if len(enemies) == 0 and current_wave < MAX_WAVE:
        boss_clear_menu_delay_remaining = None
        current_wave += 1
        spawn_wave(current_wave)
        pygame.event.clear()
        continue

    # Show next level menu only after boss wave is cleared
    if len(enemies) == 0 and current_wave >= MAX_WAVE:
        if boss_clear_menu_delay_remaining is None:
            boss_clear_menu_delay_remaining = BOSS_CLEAR_MENU_DELAY_MS
        else:
            boss_clear_menu_delay_remaining -= dt

        if boss_clear_menu_delay_remaining > 0:
            # Keep rendering game frames so boss explosion animation can play first
            pass
        else:
            boss_clear_menu_delay_remaining = None
            next_level_screen = NextLevel(
                current_level=current_wave,
                max_level=MAX_WAVE,
                display_current_level=1,
                display_next_level=2,
            )
            next_level_action = next_level_screen.run()

            if isinstance(next_level_action, int):
                current_wave = next_level_action
                spawn_wave(current_wave)
                pygame.event.clear()
            elif next_level_action == "settings":
                pass
            elif next_level_action in ("quit", "game_completed"):
                run = False

            continue

    # Tarkista osumat vihollisten ja pelaajan välillä
    if enemy_hit_cooldown <= 0:
        for enemy in enemies:
            if player.rect.colliderect(enemy.rect):
                # Compute separation normal from enemy to player
                p_pos = pygame.Vector2(player.rect.center)
                e_pos = pygame.Vector2(enemy.rect.center)
                diff = p_pos - e_pos
                if diff.length_squared() == 0:
                    # fallback small random vector to avoid zero division
                    diff = pygame.Vector2(random.uniform(-1.0, 1.0), random.uniform(-1.0, 1.0))
                normal = diff.normalize()
                # Compute desired separation to place ships at touching radii
                try:
                    p_radius = get_collision_radius(player)
                except Exception:
                    p_radius = max(player.rect.width, player.rect.height) * 0.5
                try:
                    e_radius = get_collision_radius(enemy)
                except Exception:
                    e_radius = max(enemy.rect.width, enemy.rect.height) * 0.5

                desired_dist = p_radius + e_radius + 2.0

                # masses (defaults)
                m1 = float(getattr(player, 'mass', 3.0))
                m2 = float(getattr(enemy, 'mass', 1.0))
                total = max(1e-6, (m1 + m2))

                dist = diff.length()
                overlap = desired_dist - dist

                if overlap > 0:
                    # move apart proportional to masses (heavier moves less)
                    p_move = normal * (overlap * (m2 / total))
                    e_move = -normal * (overlap * (m1 / total))
                    new_p = p_pos + p_move
                    new_e = e_pos + e_move
                else:
                    # already separated; nudge so centers are at desired distance (centered proportionally)
                    correction = desired_dist - dist
                    p_move = normal * (correction * (m2 / total))
                    e_move = -normal * (correction * (m1 / total))
                    new_p = p_pos + p_move
                    new_e = e_pos + e_move

                # If the enemy is essentially stationary, trigger a 2-oscillation collision bounce
                e_vel = getattr(enemy, 'vel', pygame.Vector2(0, 0))
                e_speed = 0.0
                try:
                    e_speed = float(e_vel.length())
                except Exception:
                    try:
                        e_speed = float((pygame.Vector2(e_vel)).length())
                    except Exception:
                        e_speed = 0.0

                try:
                    player.pos = pygame.Vector2(new_p)
                    player.rect.center = (int(player.pos.x), int(player.pos.y))
                except Exception:
                    try:
                        player.rect.center = (int(new_p.x), int(new_p.y))
                    except Exception:
                        pass

                # Reduce player forward speed to 30% of previous
                try:
                    if getattr(player, 'vel', None) is not None:
                        player.vel = pygame.Vector2(player.vel) * 0.3
                except Exception:
                    pass

                # Stationary enemy: start a bounce animation that oscillates twice and then settles at new_e
                if e_speed < 1.0:
                    try:
                        # initial_disp = current_pos - base_pos so that position at t=0 equals current pos
                        init_disp = pygame.Vector2(e_pos) - pygame.Vector2(new_e)
                        # start collision bounce: 2 oscillations, gentle damping, duration ~1.6s
                        enemy.start_collision_bounce(new_e, init_disp, duration=1.6, oscillations=2.0, damping=2.2)
                        # ensure AI doesn't move during this (handled by collision_bounce_active)
                        try:
                            enemy.vel = pygame.Vector2(0, 0)
                        except Exception:
                            pass
                    except Exception:
                        # fallback: anchor as before
                        try:
                            if hasattr(enemy, 'pos'):
                                enemy.pos = pygame.Vector2(new_e)
                                enemy.rect.center = (int(enemy.pos.x), int(enemy.pos.y))
                            else:
                                enemy.rect.center = (int(new_e.x), int(new_e.y))
                            enemy.collision_bounce_locked = True
                            enemy.collision_bounce_timer = getattr(enemy, 'collision_bounce_duration', 1.3)
                            enemy.collision_bounce_target = pygame.Vector2(new_e)
                            try:
                                enemy.vel = pygame.Vector2(0, 0)
                            except Exception:
                                pass
                        except Exception:
                            pass
                else:
                    # moving enemy: apply an impulse so both ships are pushed apart
                    try:
                        # ensure player is at new_p (nudge)
                        try:
                            player.pos = pygame.Vector2(new_p)
                            player.rect.center = (int(player.pos.x), int(player.pos.y))
                        except Exception:
                            try:
                                player.rect.center = (int(new_p.x), int(new_p.y))
                            except Exception:
                                pass

                        # Try to use the generic apply_impact impulse routine
                        try:
                            apply_impact(player, enemy, elasticity=0.85)
                        except Exception:
                            # fallback: nudge enemy position proportionally (already computed new_e)
                            try:
                                if hasattr(enemy, 'pos'):
                                    enemy.pos = pygame.Vector2(new_e)
                                    enemy.rect.center = (int(enemy.pos.x), int(enemy.pos.y))
                                else:
                                    enemy.rect.center = (int(new_e.x), int(new_e.y))
                            except Exception:
                                pass

                        # small separation step to avoid re-sticking
                        try:
                            separate(player, enemy, frac=0.9)
                        except Exception:
                            pass
                    except Exception:
                        pass

                # Debug: print collision sizing information when player takes damage
                try:
                    collision_dist = float(dist)
                except Exception:
                    collision_dist = float(pygame.Vector2(player.rect.center).distance_to(pygame.Vector2(enemy.rect.center)))
                try:
                    print(f"PLAYER DAMAGE: RadiusPlayer={p_radius:.1f} RadiusEnemy={e_radius:.1f} CollisionDistance={collision_dist:.1f} player.rect={player.rect} enemy.rect={enemy.rect}")
                except Exception:
                    pass

                # Deduct life (prefer player's health) and start cooldown
                try:
                    if hasattr(player, 'health'):
                        player.health = max(0, int(player.health) - 1)
                        lives = player.health
                        try:
                            if hasattr(player, 'trigger_hit_animation'):
                                player.trigger_hit_animation()
                        except Exception:
                            pass
                    else:
                        lives -= 1
                except Exception:
                    lives -= 1
                enemy_hit_cooldown = enemy_hit_cooldown_duration
                break  # only one collision event per cooldown

    # Päivitä cooldown
    if enemy_hit_cooldown > 0:
        enemy_hit_cooldown -= dt


# Tarkista pelin loppu
    if lives <= 0:
        game_over_screen.show(X, Y)
        game_over = game_over_screen.run()

        if game_over == "play_again":
            reset_game()
            pygame.event.clear()

        elif game_over == "main_menu":
            menu = MainMenu()
            result = menu.run()
            if result != "start_game":
                run = False
            else:
                reset_game()
            pygame.event.clear()

        elif game_over == "quit":
            run = False

        continue  # tämä on ok: hyppää seuraavaan frameen kuoleman jälkeen

    for e in enemies:
        e.draw(screen, camera_x, camera_y)

    # Debug: draw collision rectangles and collision radii (camera-relative)
    if DEBUG_DRAW_COLLISIONS:
        try:
            # player rect (red)
            pygame.draw.rect(screen, (255, 0, 0), player.rect.move(-camera_x, -camera_y), 1)
        except Exception:
            pass
        for e in enemies:
            try:
                # enemy rect (green)
                pygame.draw.rect(screen, (0, 200, 0), e.rect.move(-camera_x, -camera_y), 1)
            except Exception:
                pass
            try:
                # draw collision radii as circles (semi-transparent outlines)
                pr = int(get_collision_radius(player))
                er = int(get_collision_radius(e))
                pc = (int(player.rect.centerx - camera_x), int(player.rect.centery - camera_y))
                ec = (int(e.rect.centerx - camera_x), int(e.rect.centery - camera_y))
                pygame.draw.circle(screen, (255, 100, 100), pc, max(1, pr), 1)
                pygame.draw.circle(screen, (100, 255, 100), ec, max(1, er), 1)
            except Exception:
                pass

    # Muzzle (paikka mistä ammus lähtee vihollisesta)
    for m in list(muzzles):
        m.update(dt)
        if getattr(m, 'dead', False):
            muzzles.remove(m)
            continue
        m.draw(screen, camera_x, camera_y)

    #Päivitä osumat ja tee räjähdysanimaatio.
    for b in list(enemy_bullets):
        b.update(dt, world_rect)
        if getattr(b, 'dead', False):
            enemy_bullets.remove(b)
            continue
        # törmäys pelaajaan. Trigger räjähdys ja poista ammus. Pelaaja menettää elämän.
        if getattr(b, 'state', '') == 'flight' and b.rect.colliderect(player.rect):
            b.explode()
            enemy_bullets.remove(b)
            # decrement player's health if available, else decrement lives
            if hasattr(player, 'health'):
                player.health = max(0, int(player.health) - 1)
                lives = player.health
                try:
                    if hasattr(player, 'trigger_hit_animation'):
                        player.trigger_hit_animation()
                except Exception:
                    pass
            else:
                lives -= 1
            continue

    # Vihollisen ammuksen piirtoa
    for b in enemy_bullets:
        b.draw(screen, camera_x, camera_y)


    # Piirrä pelaaja kameran suhteessa
    player.draw(screen, camera_x, camera_y)

    # Näytä pisteet vasemmassa yläkulmassa.
    pistejarjestelma.show_score(10, 10, pygame.font.SysFont('Arial', 24), screen)

    # Näytä elämät / health sprites oikeassa yläkulmassa
    font = pygame.font.SysFont('Arial', 24)
    try:
        # prefer player's health if present
        cur_health = lives
        max_h = 5
        if hasattr(player, 'health'):
            cur_health = int(max(0, min(player.health, getattr(player, 'max_health', 5))))
            max_h = int(getattr(player, 'max_health', 5))

        hud_img = None
        if isinstance(health_imgs, dict):
            if max_h > 0 and max_h != 5:
                slot = int(round((cur_health / max_h) * 5))
            else:
                slot = int(max(0, min(cur_health, 5)))
            hud_img = health_imgs.get(slot)

        if hud_img:
            try:
                pos = HEALTH_ICON_POS
                screen.blit(hud_img, pos)
            except Exception:
                screen.blit(hud_img, HEALTH_ICON_POS)
        else:
            lives_text = font.render(f"Elämät: {cur_health}", True, (255, 255, 255))
            screen.blit(lives_text, (X - 200, 10))
    except Exception:
        lives_text = font.render(f"Elämät: {lives}", True, (255, 255, 255))
        screen.blit(lives_text, (X - 200, 10))

    # Pause overlay
    if pause:
        from Valikot.PauseMenu import PauseMenu
        pause_menu = PauseMenu()
        # Piirrä nykyinen pelinäkymä taustaksi
        background_surface = screen.copy()
        action = pause_menu.run(background_surface)
        if action == "quit":
            run = False
            pause = False
        elif action == "continue":
            pause = False
        elif action == "settings":
            # settings_menu_main() kutsutaan jo PauseMenu-luokassa
            pass
        continue  # Älä suorita muuta pelisilmukkaa kun pause päällä
    # Päivitä näyttö

    # handle explosions via manager
    explosion_manager.update(dt)
    explosion_manager.draw(screen, camera_x, camera_y)
    pygame.display.update()

Legacy loop snapshot.
Current integration path:
- State system creates `Game` directly (see States/PlayState.py)
- Old function-style calls use wrappers: `init/update/draw/is_running`
"""
