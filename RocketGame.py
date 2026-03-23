"""
Module: RocketGame.py
Dependencies: pygame, os, random, SpriteSettings, PLAYER_LUOKAT.Player2 (Player2), EnemyAI (StraightEnemy, CircleEnemy), boss_enemy (BossEnemy), Points
Provides: main game loop, loads sprites and spawns enemies/boss, handles collisions and draws
Uses: EnemyHelpers for specific explosion spawn when needed
"""

import sys
import os
from Enemies import enemy
import pygame
import random
from Enemies.EnemyAI import StraightEnemy, CircleEnemy, DownEnemy, UpEnemy, ZigZagEnemy, ChaseEnemy
from boss_enemy import BossEnemy
from points import Points
sys.path.append(os.path.dirname(__file__))
from player2 import Player2
from Valikot.NextLevel import NextLevel
from Valikot.gameOver import GameOverScreen
from leaderboard import Leaderboard
from SpriteSettings import SpriteSettings
from explosion import ExplosionManager
from Collision.collisions import SpatialHash, apply_impact, separate, _get_pos, get_collision_radius
from ui import init_enemy_health_bars, draw_hud
import planets
from Meteor.meteor import Meteor
from Tasot.Taso1 import spawn_wave_taso1
# Import other level wave-spawn functions as they're created
try:
    from Tasot.Taso2 import spawn_wave_taso2
except ImportError:
    spawn_wave_taso2 = None
try:
    from Tasot.Taso3 import spawn_wave_taso3
except ImportError:
    spawn_wave_taso3 = None
try:
    from Tasot.Taso4 import spawn_wave_taso4
except ImportError:
    spawn_wave_taso4 = None
try:
    from Tasot.Taso5 import spawn_wave_taso5
except ImportError:
    spawn_wave_taso5 = None

from States.GameStateManager import GameStateManager
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
BOSS_EXPLOSION_HOLD_MS = 900
PLAYER_DEATH_HOLD_MS = 1100
PLAYER_DEATH_EXPLOSION_FPS = 12
PLAYER_DESTROYED_FRAME_MS = 95


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

    def __init__(self, screen, level_number=1):
        self.screen = screen
        self.level_number = level_number  # Track which level this instance manages (1-5)
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
        self.meteors = []  # Static meteor obstacles
        self.boss = None
        self.current_wave = 1
        self.MAX_WAVE = 4  # Each level has up to 4 waves (1-3 normal, 4 = boss)
        self.wave_cleared = False
        self.boss_clear_menu_delay_remaining = None
        self.player_death_menu_delay_remaining = None
        self.level_completed = False
        self.game_over = False
        self.lives = 3
        self.enemy_hit_cooldown = 0
        self.enemy_hit_cooldown_duration = 1000
        self.pistejarjestelma = None
        self.leaderboard = Leaderboard()
        try:
            self.leaderboard.load_from_file(os.path.join(os.path.dirname(__file__), 'leaderboard.json'))
        except FileNotFoundError:
            pass

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
        self.base_path = base_path
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

        # Boss-kuva tason mukaan
        boss_files = {
            1: "12.png",
            2: "13.png",   
            #3: "14.png",
            #4: "15.png",
            #5: "16.png",
}

        boss_file = boss_files.get(self.level_number, "12.png")

        self.boss_image = pygame.transform.scale(
            pygame.image.load(os.path.join(viholliset_path, boss_file)).convert_alpha(),
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

        # Pelaajan health HUD kuvat: images/elementit/15.png .. 20.png
        self.health_imgs = {}
        health_dir = os.path.join(base_path, 'images', 'elementit')
        for h in range(0, 6):
            img_index = 15 + h
            path = os.path.join(health_dir, f"{img_index}.png")
            try:
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.scale(img, HEALTH_ICON_SCALE_SIZE)
                self.health_imgs[h] = img
            except Exception:
                self.health_imgs[h] = None

        # Initialize boss/enemy health bar images used by BossEnemy.
        try:
            init_enemy_health_bars(base_path)
        except Exception:
            try:
                init_enemy_health_bars()
            except Exception:
                pass

        # Ensure explosion animations are loaded before gameplay starts.
        # Without frames, spawn_enemy/spawn_boss are no-ops.
        try:
            self.explosion_manager.load_all_defaults()
        except Exception:
            pass

    def init_game_objects(self):
        """Alusta pelaaja, pistejärjestelmä ja ensimmäinen wave"""
        self.pistejarjestelma = Points()

        player_ship = 'FIGHTER'
        player_start_x = self.tausta_leveys // 2
        player_start_y = self.tausta_korkeus // 2
        player_scale_factor = 1

        self.player = Player2(player_ship, player_scale_factor, player_start_x, player_start_y, max_health=5)
        if hasattr(self.player, 'destroyed_anim_speed'):
            self.player.destroyed_anim_speed = PLAYER_DESTROYED_FRAME_MS

        apply_hitbox(self.player, HITBOX_SIZE_PLAYER)
        self.lives = int(getattr(self.player, 'health', getattr(self.player, 'max_health', 5)))
        self.spawn_wave(self.current_wave)

    def reset_game(self):
        """Resettaa pelin tilan ja pelaajan"""
        self.current_wave = 1
        self.wave_cleared = False
        self.boss_clear_menu_delay_remaining = None
        self.player_death_menu_delay_remaining = None
        self.level_completed = False
        self.game_over = False
        self.enemies.clear()
        self.enemy_bullets.clear()
        self.muzzles.clear()
        self.meteors.clear()
        self.collisions.clear()
        self.player.health = getattr(self.player, 'max_health', 5)
        if hasattr(self.player, 'is_destroyed'):
            self.player.is_destroyed = False
        if hasattr(self.player, 'destroyed_anim_timer'):
            self.player.destroyed_anim_timer = 0
        if hasattr(self.player, 'destroyed_frame_index'):
            self.player.destroyed_frame_index = 0
        if hasattr(self.player, 'destroyed_angle'):
            self.player.destroyed_angle = float(getattr(self.player, 'angle', 0.0))
        self.lives = self.player.health
        self.spawn_wave(self.current_wave)
        self.pistejarjestelma = Points()
        pygame.event.clear()

    def spawn_wave(self, wave_num):
        """Spawnaa viholliset wave-numeroon ja level-numeroon perustuen"""
        self.enemies.clear()

        # Dispatch to correct level's spawn function
        spawn_func = None
        if self.level_number == 1:
            spawn_func = spawn_wave_taso1
        elif self.level_number == 2 and spawn_wave_taso2:
            spawn_func = spawn_wave_taso2
        elif self.level_number == 3 and spawn_wave_taso3:
            spawn_func = spawn_wave_taso3
        elif self.level_number == 4 and spawn_wave_taso4:
            spawn_func = spawn_wave_taso4
        elif self.level_number == 5 and spawn_wave_taso5:
            spawn_func = spawn_wave_taso5

        if spawn_func:
            handled = spawn_func(
                game=self,
                wave_num=wave_num,
                apply_hitbox=apply_hitbox,
                hitbox_enemy=HITBOX_SIZE_ENEMY,
                hitbox_boss=HITBOX_SIZE_BOSS,
                straight_enemy_cls=StraightEnemy,
                circle_enemy_cls=CircleEnemy,
                boss_enemy_cls=BossEnemy,
                down_enemy_cls=DownEnemy,
                up_enemy_cls=UpEnemy,
                zigzag_enemy_cls=ZigZagEnemy,
                chase_enemy_cls=ChaseEnemy,
            )
            if handled:
                return

        # Fallback: if no level handler or unhandled wave, spawn nothing
        # (Level 2-5 will use their own spawn logic when implemented)

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

                    if bullet in self.player.weapons.bullets:
                        self.player.weapons.bullets.remove(bullet)

                    if isinstance(enemy, BossEnemy):
                        damage = getattr(bullet, "damage", 1)
                        died = enemy.take_hit(damage)

                        if died:
                            self.explosion_manager.spawn_boss(enemy.rect.center, fps=20)
                            if enemy in self.enemies:
                                self.enemies.remove(enemy)
                                self.pistejarjestelma.lisaa_piste(5)
                        else:
                            self.explosion_manager.spawn_hit(impact_pos, fps=24)

                    else:
                        damage = getattr(bullet, "damage", 1)

                        if hasattr(enemy, "hp"):
                            enemy.hp -= damage
                            if enemy.hp <= 0:
                                self.explosion_manager.spawn_enemy(enemy.rect.center, fps=20)
                                if enemy in self.enemies:
                                    self.enemies.remove(enemy)
                                self.pistejarjestelma.lisaa_piste(1)
                            else:
                                self.explosion_manager.spawn_hit(impact_pos, fps=24)
                        else:
                            self.explosion_manager.spawn_enemy(impact_pos, fps=20)
                    
                            if enemy in self.enemies:
                                self.enemies.remove(enemy)
                            self.pistejarjestelma.lisaa_piste(1)

                    break

        for b in list(self.enemy_bullets):
            b.update(self.dt, pygame.Rect(0,0,self.tausta_leveys,self.tausta_korkeus))
            if getattr(b,'dead',False):
                self.enemy_bullets.remove(b)
            elif (
                getattr(b,'state','')=='flight'
                and b.rect.colliderect(self.player.rect)
                and self.lives > 0
                and self.player_death_menu_delay_remaining is None
            ):
                b.explode()
                self.enemy_bullets.remove(b)
                self.player.health = max(0, self.player.health-1)
                self.lives = self.player.health
                try:
                    if hasattr(self.player, 'trigger_hit_animation'):
                        self.player.trigger_hit_animation()
                except Exception:
                    pass

        # Meteor collision handling
        # Player vs meteors: player loses health on collision
        meteor_hit_cooldown = getattr(self, '_meteor_hit_cooldown', 0)
        if meteor_hit_cooldown <= 0 and self.lives > 0 and self.player_death_menu_delay_remaining is None:
            for meteor in self.meteors:
                if self.player.rect.colliderect(meteor.rect):
                    self.player.health = max(0, self.player.health - 1)
                    self.lives = self.player.health
                    try:
                        if hasattr(self.player, 'trigger_hit_animation'):
                            self.player.trigger_hit_animation()
                    except Exception:
                        pass
                    
                    # Apply knockback to player
                    player_center = pygame.Vector2(self.player.rect.center)
                    meteor_center = pygame.Vector2(meteor.rect.center)
                    direction = player_center - meteor_center
                    if direction.length_squared() == 0:
                        direction = pygame.Vector2(1, 0)
                    else:
                        direction = direction.normalize()
                    
                    if hasattr(self.player, "vel"):
                        self.player.vel = direction * 420
                    
                    if hasattr(self.player, "collision_bounce_locked"):
                        self.player.collision_bounce_locked = True
                        self.player.collision_bounce_timer = 0.18
                    
                    self._meteor_hit_cooldown = self.enemy_hit_cooldown_duration
                    break
        
        if meteor_hit_cooldown > 0:
            self._meteor_hit_cooldown = max(0, meteor_hit_cooldown - self.dt)
        
        # Player bullets vs meteors: bullets pass through (no damage to meteors)
        # Meteors are invulnerable, so bullets just pass through them
        for meteor in self.meteors:
            for bullet in list(self.player.weapons.bullets):
                if bullet.rect.colliderect(meteor.rect):
                    # Remove bullet that hits meteor
                    if bullet in self.player.weapons.bullets:
                        self.player.weapons.bullets.remove(bullet)

        # Kontakti-osuma vihollisen ja pelaajan välillä cooldownilla.
        if self.enemy_hit_cooldown <= 0 and self.lives > 0 and self.player_death_menu_delay_remaining is None:
            for enemy in self.enemies:
                if self.player.rect.colliderect(enemy.rect):
                    self.player.health = max(0, int(getattr(self.player, 'health', self.lives)) - 1)
                    self.lives = self.player.health

                    try:
                        if hasattr(self.player, 'trigger_hit_animation'):
                            self.player.trigger_hit_animation()
                    except Exception:
                        pass

                    player_center = pygame.Vector2(self.player.rect.center)
                    enemy_center = pygame.Vector2(enemy.rect.center)
                    direction = player_center - enemy_center

                    if direction.length_squared() == 0:
                        direction = pygame.Vector2(1, 0)
                    else:
                        direction = direction.normalize()

                # Smooth knockback pelaajalle
                    if hasattr(self.player, "vel"):
                        self.player.vel = direction * 420

                # Lukitse ohjaus hetkeksi, jotta knockback ehtii näkyä
                    if hasattr(self.player, "collision_bounce_locked"):
                        self.player.collision_bounce_locked = True
                        self.player.collision_bounce_timer = 0.18
                    # estä vihollista jahtaamasta heti takaisin
                    if hasattr(enemy, "hit_player_cooldown"):
                        enemy.hit_player_cooldown = 8

                    self.enemy_hit_cooldown = self.enemy_hit_cooldown_duration
                    break
        if self.enemy_hit_cooldown > 0:
            self.enemy_hit_cooldown -= self.dt
        

        # Wave progression: wave 1 -> 2 -> 3 -> boss (4).
        if len(self.enemies) == 0 and not self.level_completed and self.lives > 0:
            if self.current_wave < self.MAX_WAVE:
                self.current_wave += 1
                self.enemy_bullets.clear()
                self.muzzles.clear()
                self.spawn_wave(self.current_wave)
            else:
                # Boss beaten: let explosion animation play briefly before
                # moving to level complete state.
                if self.boss_clear_menu_delay_remaining is None:
                    self.boss_clear_menu_delay_remaining = BOSS_EXPLOSION_HOLD_MS

        if self.lives <= 0 and self.player_death_menu_delay_remaining is None:
            self.leaderboard.add_score("", self.pistejarjestelma.hae_pisteet())
            self.leaderboard.save_to_file(os.path.join(self.base_path, 'leaderboard.json'))
            print(self.leaderboard.get_player_scores())

            if hasattr(self.player, 'is_destroyed'):
                self.player.is_destroyed = True
            if hasattr(self.player, 'destroyed_anim_timer'):
                self.player.destroyed_anim_timer = 0
            if hasattr(self.player, 'destroyed_frame_index'):
                self.player.destroyed_frame_index = 0
            if hasattr(self.player, 'destroyed_angle'):
                self.player.destroyed_angle = float(getattr(self.player, 'angle', 0.0))
            if hasattr(self.player, 'vel'):
                self.player.vel = pygame.Vector2(0, 0)

            # Keep Game Over delay long enough for the slower destroyed + explosion animations.
            destroyed_count = len(getattr(self.player, 'destroyed_frames', []) or getattr(self.player, 'destroyed_sprites', []))
            destroyed_speed_ms = int(getattr(self.player, 'destroyed_anim_speed', PLAYER_DESTROYED_FRAME_MS))
            destroyed_total_ms = destroyed_count * max(1, destroyed_speed_ms)
            self.player_death_menu_delay_remaining = max(
                PLAYER_DEATH_HOLD_MS,
                destroyed_total_ms + 180,
            )

            try:
                print(
                    f"[DEATH DEBUG] destroyed_frames={destroyed_count}, "
                    f"destroyed_frame_ms={destroyed_speed_ms}, "
                    f"player_explosion_frames=0, "
                    f"player_explosion_fps=0, "
                    f"hold_ms={self.player_death_menu_delay_remaining}"
                )
            except Exception:
                pass

        # Räjähdykset
        self.explosion_manager.update(self.dt)

        if self.boss_clear_menu_delay_remaining is not None:
            self.boss_clear_menu_delay_remaining -= self.dt
            if self.boss_clear_menu_delay_remaining <= 0:
                self.level_completed = True
                self.running = False

        if self.player_death_menu_delay_remaining is not None:
            self.player_death_menu_delay_remaining -= self.dt
            if self.player_death_menu_delay_remaining <= 0:
                self.game_over = True
                self.running = False

    def draw(self, target_screen):
        """Piirrä kaikki peliobjektit annettuun ruutuun"""
        self.screen = target_screen
        self.screen.blit(self.tausta, (0,0), area=(self.camera_x, self.camera_y, X, Y))

        for kuva, (x, y) in zip(self.planeetat, self.planeetta_paikat):
            self.screen.blit(kuva, (x - self.camera_x, y - self.camera_y))

        for meteor in self.meteors:
            meteor.draw(self.screen, self.camera_x, self.camera_y)

        for e in self.enemies:
            e.draw(self.screen, self.camera_x, self.camera_y)

        # Boss HP barit vasempaan yläkulmaan
        for idx, e in enumerate([be for be in self.enemies if isinstance(be, BossEnemy)]):
            e.draw_health_bar(self.screen, idx)

        for b in self.enemy_bullets:
            b.draw(self.screen, self.camera_x, self.camera_y)

        for m in self.muzzles:
            m.draw(self.screen, self.camera_x, self.camera_y)

        self.player.draw(self.screen, self.camera_x, self.camera_y)
        self.explosion_manager.draw(self.screen, self.camera_x, self.camera_y)

        self.pistejarjestelma.show_score(10,10, pygame.font.SysFont('Arial',24), self.screen)
        draw_hud(self.screen, X, Y, self.player, self.lives, self.health_imgs, HEALTH_ICON_POS)


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