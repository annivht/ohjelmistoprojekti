"""
Module: RocketGame.py
Dependencies: pygame, os, random, SpriteSettings, PLAYER_LUOKAT.Player2 (Player2), EnemyAI (StraightEnemy, CircleEnemy), boss_enemy (BossEnemy), Points
Provides: main game loop, loads sprites and spawns enemies/boss, handles collisions and draws
Uses: EnemyHelpers for specific explosion spawn when needed
"""

import sys
import os
import time
import math
from types import SimpleNamespace
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
from Physics.box2d_world import Box2DPhysicsWorld, CollisionCategory
from physics_settings import load_physics_settings
import planets
from Meteor.meteor import Meteor
from Hazards.hazard_system import HazardSystem
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
try:
    from Tasot.TestLevel import spawn_wave_test
except ImportError:
    spawn_wave_test = None
try:
    from Tasot.TestLevel2 import spawn_wave_test2
except ImportError:
    spawn_wave_test2 = None

from States.GameStateManager import GameStateManager
# Näytön/HUD perusmitat
DEFAULT_VIEW_SIZE = (1600, 800)
HEALTH_ICON_SIZE = (600, 200)
HEALTH_ICON_MARGIN = 16

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
        self.view_width, self.view_height = DEFAULT_VIEW_SIZE
        self.health_icon_scale_size = HEALTH_ICON_SIZE
        self.health_icon_pos = (HEALTH_ICON_MARGIN, HEALTH_ICON_MARGIN)
        self._refresh_view_metrics()
        self.level_number = level_number  # Track which level this instance manages (1-5)
        self.is_test_level = int(level_number) == 0
        self.is_test2_level = int(level_number) == 6
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
        self.hazard_system = None
        self.boss = None
        self.current_wave = 1
        self.MAX_WAVE = 1 if (self.is_test_level or self.is_test2_level) else 4  # Test levels are persistent.
        self.wave_cleared = False
        self.boss_clear_menu_delay_remaining = None
        self.player_death_menu_delay_remaining = None
        self.level_completed = False
        self.game_over = False
        self.lives = 3
        self.enemy_hit_cooldown = 0
        self.enemy_hit_cooldown_duration = 1400
        self.enemy_calm_timer_ms = 0
        self.enemy_calm_duration_ms = 2400
        self.enemy_calm_shoot_scale = 0.45
        self._boss_storm_active = False
        self._boss_storm_next_ms = None
        self._boss_storm_hide_remaining_ms = 0
        self._boss_storm_spawn_timer_ms = 0
        self._boss_storm_spawn_interval_ms = 260
        self._test2_shower_cd_ms = random.randint(2200, 4200)
        self._test2_storm_phase = "idle"
        self._test2_storm_side = "top"
        self._test2_storm_timer_ms = 0
        self._test2_storm_burst_remaining = 0
        self._test2_storm_burst_step_ms = 0
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
        self.DEBUG_DRAW_ENEMY_FACING = os.environ.get('RG_DEBUG_ENEMY_FACING', '0').strip() in ('1', 'true', 'True', 'yes', 'on')
        self.USE_SPATIAL_COLLISIONS = True
        self.physics_world = None
        self.physics_metrics = {
            'physics_step_ms': 0.0,
            'substeps': 0,
            'contacts': 0,
            'profile': 'disabled',
            'fixed_dt': 0.0,
            'frame_ms': 0.0,
        }
        self.show_physics_stats = False #fysiikka-debug tiedot
        self.physics_font = pygame.font.SysFont('Consolas', 16)
        self.enemy_debug_font = pygame.font.SysFont('Consolas', 14)
        self.user_physics_settings = load_physics_settings()
        env_profile = os.environ.get('RG_PHYSICS_PROFILE', '').strip().lower()
        self.physics_profile_name = env_profile or str(self.user_physics_settings.get('physics_profile', 'balanced')).strip().lower() or 'balanced'

        try:
            self.physics_world = Box2DPhysicsWorld(profile_name=self.physics_profile_name)
            self.physics_metrics['profile'] = self.physics_profile_name
            self.physics_metrics['fixed_dt'] = self.physics_world.fixed_dt
        except Exception:
            self.physics_world = None

        # Lataa tausta ja planeetat
        self._load_assets()

        if self.is_test_level:
            self.hazard_system = HazardSystem(
                world_size=(self.tausta_leveys, self.tausta_korkeus),
                sprite_root=os.path.join(self.base_path, "images", "Space-Shooter_objects"),
                config={
                    "enabled": True,
                    "fuse_seconds": 3.0,
                    "warning_seconds": 1.0,
                    "bomb_radius": 150.0,
                    "bomb_damage": 1,
                    "bomb_family": "2",
                    "bomb_sprite_size": 72,
                    "meteor_spawn_rate": 1.7,
                    "max_active_meteors": 10,
                    "enemy_drop_chance": 0.27,
                    "enemy_drop_cooldown": 0.7,
                    "boss_drop_interval_min": 4.0,
                    "boss_drop_interval_max": 6.0,
                    "shockwave_max_radius_mult": 1.5,
                    "shockwave_speed": 430.0,
                    "shockwave_band": 46.0,
                    "shockwave_push": 480.0,
                },
            )
            # Keep legacy access working for existing code that uses self.meteors.
            self.meteors = self.hazard_system.meteors
        elif self.is_test2_level:
            self.hazard_system = HazardSystem(
                world_size=(self.tausta_leveys, self.tausta_korkeus),
                sprite_root=os.path.join(self.base_path, "images", "Space-Shooter_objects"),
                config={
                    "enabled": True,
                    "fuse_seconds": 2.8,
                    "warning_seconds": 1.0,
                    "bomb_radius": 145.0,
                    "bomb_damage": 1,
                    "bomb_family": "2",
                    "bomb_sprite_size": 64,
                    "meteor_spawn_rate": 9999.0,
                    "max_active_meteors": 26,
                    "enemy_drop_chance": 0.18,
                    "enemy_drop_cooldown": 1.0,
                    "pickup_drop_chance": 0.08,
                    "boss_drop_interval_min": 4.8,
                    "boss_drop_interval_max": 7.2,
                    "shockwave_max_radius_mult": 1.45,
                    "shockwave_speed": 410.0,
                    "shockwave_band": 42.0,
                    "shockwave_push": 430.0,
                },
            )
            self.meteors = self.hazard_system.meteors
        elif int(self.level_number) == 3:
            # Level 3 uses the same meteor visuals/physics family as test level,
            # but keeps hazards meteor-only (no bomb/pickup gameplay there).
            self.hazard_system = HazardSystem(
                world_size=(self.tausta_leveys, self.tausta_korkeus),
                sprite_root=os.path.join(self.base_path, "images", "Space-Shooter_objects"),
                config={
                    "enabled": True,
                    "meteor_spawn_rate": 9999.0,
                    "max_active_meteors": 40,
                    "enemy_drop_chance": 0.0,
                    "pickup_drop_chance": 0.0,
                    "boss_drop_interval_min": 9999.0,
                    "boss_drop_interval_max": 9999.0,
                },
            )
            self.meteors = self.hazard_system.meteors

        # Alusta pelaaja ja ensimmäinen wave
        self.init_game_objects()

    def _refresh_view_metrics(self):
        """Sync cached viewport/HUD metrics from current render target size."""
        old_w = int(getattr(self, "view_width", 0))
        old_h = int(getattr(self, "view_height", 0))
        w, h = self.screen.get_size()
        self.view_width = max(1, int(w))
        self.view_height = max(1, int(h))

        max_w = max(1, self.view_width - 2 * HEALTH_ICON_MARGIN)
        max_h = max(1, self.view_height - 2 * HEALTH_ICON_MARGIN)
        scale = min(max_w / HEALTH_ICON_SIZE[0], max_h / HEALTH_ICON_SIZE[1], 1.0)
        self.health_icon_scale_size = (
            max(1, int(HEALTH_ICON_SIZE[0] * scale)),
            max(1, int(HEALTH_ICON_SIZE[1] * scale)),
        )
        self.health_icon_pos = (
            self.view_width - self.health_icon_scale_size[0] - HEALTH_ICON_MARGIN,
            HEALTH_ICON_MARGIN,
        )
        return old_w != self.view_width or old_h != self.view_height

    def _rescale_assets_for_view(self):
        """Resize view-dependent assets after display mode/size changes."""
        if hasattr(self, "tausta_source") and self.tausta_source is not None:
            self.tausta = pygame.transform.scale(self.tausta_source, (self.view_width, self.view_height))
            self.tausta_leveys, self.tausta_korkeus = self.tausta.get_size()

        raw_icons = getattr(self, "health_raw_imgs", {})
        if raw_icons:
            self.health_imgs = {}
            for hp, raw in raw_icons.items():
                if raw is None:
                    self.health_imgs[hp] = None
                else:
                    self.health_imgs[hp] = pygame.transform.scale(raw, self.health_icon_scale_size)

        if self.hazard_system is not None:
            self.hazard_system.world_rect.size = (self.tausta_leveys, self.tausta_korkeus)

        if self.player is not None:
            px, py = self.player.rect.center
            px = max(0, min(px, self.tausta_leveys))
            py = max(0, min(py, self.tausta_korkeus))
            self.player.rect.center = (px, py)

        max_cam_x = max(0, self.tausta_leveys - self.view_width)
        max_cam_y = max(0, self.tausta_korkeus - self.view_height)
        self.camera_x = max(0, min(self.camera_x, max_cam_x))
        self.camera_y = max(0, min(self.camera_y, max_cam_y))

    def _load_assets(self):
        """Lataa tausta, vihollisten kuvat ja planeetat"""
        base_path = os.path.dirname(__file__)
        self.base_path = base_path
        self.tausta_source = pygame.image.load(os.path.join(base_path,'images','taustat','avaruus.png')).convert()
        self.tausta = pygame.transform.scale(self.tausta_source, (self.view_width, self.view_height))
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
        self.health_raw_imgs = {}
        self.health_imgs = {}
        health_dir = os.path.join(base_path, 'images', 'elementit')
        for h in range(0, 6):
            img_index = 15 + h
            path = os.path.join(health_dir, f"{img_index}.png")
            try:
                img = pygame.image.load(path).convert_alpha()
                self.health_raw_imgs[h] = img
                self.health_imgs[h] = pygame.transform.scale(img, self.health_icon_scale_size)
            except Exception:
                self.health_raw_imgs[h] = None
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
        self._init_player_physics()
        self.lives = int(getattr(self.player, 'health', getattr(self.player, 'max_health', 5)))
        self.spawn_wave(self.current_wave)

    def _init_player_physics(self):
        if self.physics_world is None or self.player is None:
            return

        old_body = self.physics_world.get_body(self.player)
        if old_body is not None:
            self.physics_world.remove_entity(self.player)

        radius = max(8, int(getattr(self.player, 'collision_radius', 24)))
        body = self.physics_world.add_circle_body(
            self.player,
            radius_px=radius,
            mass=1.8,
            dynamic=True,
            bullet=False,
            category=CollisionCategory.PLAYER,
            mask=(CollisionCategory.ENEMY | CollisionCategory.METEOR | CollisionCategory.SENSOR),
        )
        speed_mul = float(self.user_physics_settings.get('speed_multiplier', 1.0))
        turn_mul = float(self.user_physics_settings.get('turn_multiplier', 1.0))
        base_profile = self.physics_world.profile
        body.profile = SimpleNamespace(
            name=base_profile.name,
            linear_damping=base_profile.linear_damping,
            angular_damping=base_profile.angular_damping,
            thrust_force=base_profile.thrust_force * speed_mul,
            turn_torque=base_profile.turn_torque * turn_mul,
            max_speed_mps=base_profile.max_speed_mps * speed_mul,
            brake_impulse=base_profile.brake_impulse * speed_mul,
            lateral_drift_damping=base_profile.lateral_drift_damping,
        )

        self.player.sprite_angle_offset_deg = float(self.user_physics_settings.get('sprite_angle_offset_deg', 0.0))
        self.physics_metrics['profile'] = f"{self.physics_profile_name} xS{speed_mul:.2f} xT{turn_mul:.2f}"
        self.player.bind_box2d_body(body)

    def _apply_player_knockback(self, direction, speed_px_per_s, blend_with_current=0.55):
        knockback = pygame.Vector2(direction) * float(speed_px_per_s)
        current = pygame.Vector2(getattr(self.player, 'vel', pygame.Vector2(0, 0)))
        blend = max(0.0, min(1.0, float(blend_with_current)))
        final_vel = current * blend + knockback * (1.0 - blend)

        if hasattr(self.player, 'vel'):
            self.player.vel = final_vel

        if self.physics_world is not None:
            body = self.physics_world.get_body(self.player)
            if body is not None:
                body.linearVelocity = (
                    float(final_vel.x) / self.physics_world.PPM,
                    float(final_vel.y) / self.physics_world.PPM,
                )

    def _add_velocity_to_entity(self, entity, push_vec):
        """Apply a velocity push to entity types used in gameplay."""
        push = pygame.Vector2(push_vec)
        if push.length_squared() <= 1e-6:
            return

        if hasattr(entity, 'vel'):
            try:
                entity.vel = pygame.Vector2(entity.vel) + push
            except Exception:
                pass

        if hasattr(entity, 'vx'):
            try:
                entity.vx = float(getattr(entity, 'vx', 0.0)) + float(push.x)
            except Exception:
                pass
        if hasattr(entity, 'vy'):
            try:
                entity.vy = float(getattr(entity, 'vy', 0.0)) + float(push.y)
            except Exception:
                pass

    def _apply_shockwaves_from_hazards(self, waves):
        if not waves:
            return

        dt_seconds = max(0.001, self.dt / 1000.0)
        for wave in waves:
            center = pygame.Vector2(wave.get('center', (0, 0)))
            radius = float(wave.get('radius', 0.0))
            prev_radius = float(wave.get('prev_radius', 0.0))
            band = max(8.0, float(wave.get('band', 28.0)))
            strength = max(0.0, float(wave.get('strength', 280.0)))

            if radius <= 0.0 and prev_radius <= 0.0:
                continue

            low = max(0.0, min(prev_radius, radius) - band * 0.5)
            high = max(prev_radius, radius) + band * 0.5

            def _intensity_and_dir(pos):
                rel = pygame.Vector2(pos) - center
                dist = rel.length()
                if dist < 1e-6:
                    rel = pygame.Vector2(1, 0)
                    dist = 1.0
                if dist < low or dist > high:
                    return 0.0, pygame.Vector2(0, 0)
                intensity = max(0.0, 1.0 - abs(dist - radius) / (band * 0.5))
                return intensity, rel.normalize()

            # Player push
            i_player, d_player = _intensity_and_dir(self.player.rect.center)
            if i_player > 0.0:
                self._apply_player_knockback(d_player, strength * i_player, blend_with_current=0.62)

            # Enemy and meteor push
            for entity in self.enemies:
                i_ent, d_ent = _intensity_and_dir(entity.rect.center)
                if i_ent > 0.0:
                    self._add_velocity_to_entity(entity, d_ent * (strength * i_ent * 0.28))

            for meteor in self.meteors:
                i_met, d_met = _intensity_and_dir(meteor.rect.center)
                if i_met > 0.0:
                    self._add_velocity_to_entity(meteor, d_met * (strength * i_met * 0.32))

            for bullet in self.enemy_bullets:
                i_b, d_b = _intensity_and_dir(bullet.rect.center)
                if i_b > 0.0:
                    self._add_velocity_to_entity(bullet, d_b * (strength * i_b * 0.22))

    def _start_enemy_calm_period(self):
        self.enemy_calm_timer_ms = max(self.enemy_calm_timer_ms, self.enemy_calm_duration_ms)

    def _spawn_test2_meteor_from_side(self, side, tier, speed_min, speed_max):
        if self.hazard_system is None:
            return

        w = float(self.tausta_leveys)
        h = float(self.tausta_korkeus)
        speed = random.uniform(float(speed_min), float(speed_max))

        if side == "left":
            x = random.uniform(-180.0, -40.0)
            y = random.uniform(40.0, max(41.0, h * 0.78))
            vx = abs(speed) * random.uniform(0.72, 0.96)
            vy = random.uniform(-55.0, 95.0)
        elif side == "right":
            x = random.uniform(w + 40.0, w + 180.0)
            y = random.uniform(40.0, max(41.0, h * 0.78))
            vx = -abs(speed) * random.uniform(0.72, 0.96)
            vy = random.uniform(-55.0, 95.0)
        else:
            x = random.uniform(32.0, max(33.0, w - 32.0))
            y = random.uniform(-190.0, -65.0)
            vx = random.uniform(-90.0, 90.0)
            vy = abs(speed)

        self.hazard_system.spawn_meteor(tier=int(tier), center=(x, y), velocity=(vx, vy))

    def _update_test2_meteor_showers(self, dt_ms):
        if not self.is_test2_level or self.hazard_system is None:
            return

        dt_i = int(dt_ms)

        if self._test2_storm_phase == "idle":
            self._test2_shower_cd_ms -= dt_i
            if self._test2_shower_cd_ms > 0:
                return

            # Pick direction first, then telegraph the same direction with 2 small meteors.
            self._test2_storm_side = random.choice(("top", "left", "right"))
            for _ in range(2):
                self._spawn_test2_meteor_from_side(
                    self._test2_storm_side,
                    tier=1,
                    speed_min=145.0,
                    speed_max=205.0,
                )

            self._test2_storm_phase = "warning"
            self._test2_storm_timer_ms = random.randint(3000, 5000)
            return

        if self._test2_storm_phase == "warning":
            self._test2_storm_timer_ms -= dt_i
            if self._test2_storm_timer_ms > 0:
                return

            self._test2_storm_phase = "burst"
            self._test2_storm_burst_remaining = random.randint(9, 16)
            self._test2_storm_burst_step_ms = 0

        if self._test2_storm_phase == "burst":
            self._test2_storm_burst_step_ms -= dt_i
            if self._test2_storm_burst_step_ms > 0:
                return

            spawn_now = min(self._test2_storm_burst_remaining, random.randint(2, 3))
            for _ in range(spawn_now):
                tier = random.choices([1, 2, 3], weights=[0.40, 0.42, 0.18], k=1)[0]
                self._spawn_test2_meteor_from_side(
                    self._test2_storm_side,
                    tier=tier,
                    speed_min=250.0,
                    speed_max=390.0,
                )

            self._test2_storm_burst_remaining -= spawn_now
            self._test2_storm_burst_step_ms = random.randint(220, 360)

            if self._test2_storm_burst_remaining <= 0:
                self._test2_storm_phase = "idle"
                self._test2_shower_cd_ms = random.randint(9000, 15000)

    def _ensure_boss_bomb_hazards(self):
        """Enable boss bomb drops on normal levels without enabling meteor hazards."""
        if self.hazard_system is not None:
            return
        if self.is_test_level or int(self.level_number) == 3:
            return

        has_boss = any(isinstance(e, BossEnemy) for e in self.enemies)
        if not has_boss:
            return

        self.hazard_system = HazardSystem(
            world_size=(self.tausta_leveys, self.tausta_korkeus),
            sprite_root=os.path.join(self.base_path, "images", "Space-Shooter_objects"),
            config={
                "enabled": True,
                "meteor_spawn_rate": 9999.0,
                "max_active_meteors": 0,
                "enemy_drop_chance": 0.0,
                "pickup_drop_chance": 0.0,
                "boss_drop_interval_min": 3.1,
                "boss_drop_interval_max": 4.8,
                "bomb_radius": 140.0,
                "bomb_damage": 1,
                "bomb_sprite_size": 58,
            },
        )

    def _start_boss_storm_phase(self):
        if not self.is_test_level or self.hazard_system is None or self.boss is None:
            return
        if self._boss_storm_active:
            return
        if int(getattr(self.boss, 'hp', 0)) <= 0:
            return

        self._boss_storm_active = True
        self._boss_storm_hide_remaining_ms = random.randint(4200, 6200)
        self._boss_storm_spawn_timer_ms = 0
        self._boss_storm_spawn_interval_ms = random.randint(170, 280)

        if self.boss in self.enemies:
            self.enemies.remove(self.boss)

    def _end_boss_storm_phase(self):
        self._boss_storm_active = False
        self._boss_storm_hide_remaining_ms = 0
        self._boss_storm_spawn_timer_ms = 0
        self._boss_storm_next_ms = random.randint(9000, 14000)

        if self.boss is None or int(getattr(self.boss, 'hp', 0)) <= 0:
            return

        if self.boss not in self.enemies:
            return_x = random.randint(220, max(221, self.tausta_leveys - 220))
            return_y = int(max(110, min(self.tausta_korkeus * 0.35, getattr(self.boss, 'target_y', 180))))
            self.boss.rect.center = (return_x, return_y)
            self.boss.state = "active"
            if hasattr(self.boss, '_shoot_cooldown_ms'):
                self.boss._shoot_cooldown_ms = random.randint(420, 900)
            self.enemies.append(self.boss)

    def _spawn_storm_meteor(self):
        if self.hazard_system is None:
            return
        x = random.uniform(40, max(41, self.tausta_leveys - 40))
        start = (x, -70)
        velocity = (
            random.uniform(-130.0, 130.0),
            random.uniform(300.0, 520.0),
        )
        tier = random.choices([3, 2, 1], weights=[0.58, 0.28, 0.14], k=1)[0]
        self.hazard_system.spawn_meteor(tier=tier, center=start, velocity=velocity)

    def _update_boss_storm_phase(self, dt_ms):
        if not self.is_test_level or self.hazard_system is None or self.boss is None:
            return
        if int(getattr(self.boss, 'hp', 0)) <= 0:
            self._boss_storm_active = False
            return

        if self._boss_storm_active:
            self._boss_storm_hide_remaining_ms -= int(dt_ms)
            self._boss_storm_spawn_timer_ms -= int(dt_ms)

            while self._boss_storm_spawn_timer_ms <= 0:
                self._spawn_storm_meteor()
                self._boss_storm_spawn_interval_ms = random.randint(170, 280)
                self._boss_storm_spawn_timer_ms += self._boss_storm_spawn_interval_ms

            if self._boss_storm_hide_remaining_ms <= 0:
                self._end_boss_storm_phase()
            return

        if self.boss not in self.enemies:
            self.enemies.append(self.boss)

        if self._boss_storm_next_ms is None:
            self._boss_storm_next_ms = random.randint(9000, 14000)

        self._boss_storm_next_ms -= int(dt_ms)
        if self._boss_storm_next_ms <= 0:
            self._start_boss_storm_phase()

    def _calm_nearby_enemies(self, center, radius_px=260.0, cooldown_seconds=1.8):
        c = pygame.Vector2(center)
        r2 = float(radius_px) * float(radius_px)
        for enemy in self.enemies:
            try:
                d2 = (pygame.Vector2(enemy.rect.center) - c).length_squared()
            except Exception:
                continue
            if d2 <= r2 and hasattr(enemy, 'hit_player_cooldown'):
                enemy.hit_player_cooldown = max(float(getattr(enemy, 'hit_player_cooldown', 0.0)), float(cooldown_seconds))

    def _draw_physics_overlay(self, screen):
        if not self.show_physics_stats:
            return
        lines = [
            f"Physics profile: {self.physics_metrics.get('profile', 'n/a')}",
            f"Frame ms: {self.physics_metrics.get('frame_ms', 0.0):5.2f}",
            f"Physics ms: {self.physics_metrics.get('physics_step_ms', 0.0):5.2f}",
            f"Substeps: {self.physics_metrics.get('substeps', 0)}",
            f"Contacts: {self.physics_metrics.get('contacts', 0)}",
        ]
        if self.hazard_system is not None:
            lines.extend(self.hazard_system.get_debug_lines())
        y = 10
        for line in lines:
            surf = self.physics_font.render(line, True, (220, 230, 255))
            screen.blit(surf, (10, y))
            y += 18

    def _get_enemy_velocity(self, enemy):
        vel = getattr(enemy, 'vel', None)
        if vel is not None:
            try:
                return pygame.Vector2(float(vel.x), float(vel.y))
            except Exception:
                pass
        vx = float(getattr(enemy, 'vx', 0.0))
        vy = float(getattr(enemy, 'vy', 0.0))
        return pygame.Vector2(vx, vy)

    def _get_enemy_render_forward(self, enemy, vel):
        try:
            ang = float(getattr(enemy, 'display_angle', 0.0))
            forward = pygame.Vector2(math.cos(ang + math.pi / 2), math.sin(ang + math.pi / 2))
            if forward.length_squared() > 1e-6:
                return forward.normalize()
        except Exception:
            pass

        if vel.length_squared() > 1e-6:
            return vel.normalize()
        return pygame.Vector2(1, 0)

    def _draw_enemy_facing_debug(self, screen):
        if not self.DEBUG_DRAW_ENEMY_FACING:
            return

        cam = pygame.Vector2(float(self.camera_x), float(self.camera_y))
        for enemy in self.enemies:
            vel = self._get_enemy_velocity(enemy)
            forward = self._get_enemy_render_forward(enemy, vel)

            center = pygame.Vector2(float(enemy.rect.centerx), float(enemy.rect.centery))
            p0 = center - cam
            p1 = p0 + forward * 28.0

            vx = float(vel.x)
            expected_sign = 0
            if abs(vx) > 5.0:
                expected_sign = 1 if vx > 0 else -1
            facing_sign = 1 if forward.x >= 0 else -1

            mismatch = expected_sign != 0 and facing_sign != expected_sign
            color = (255, 80, 80) if mismatch else (120, 255, 140)

            pygame.draw.line(screen, color, (int(p0.x), int(p0.y)), (int(p1.x), int(p1.y)), 2)

            tip = p1
            side = pygame.Vector2(-forward.y, forward.x)
            left = tip - forward * 8.0 + side * 5.0
            right = tip - forward * 8.0 - side * 5.0
            pygame.draw.polygon(screen, color, [
                (int(tip.x), int(tip.y)),
                (int(left.x), int(left.y)),
                (int(right.x), int(right.y)),
            ])

            facing_txt = 'right' if facing_sign > 0 else 'left'
            label = f"{enemy.__class__.__name__} facing {facing_txt} | vx={vx:+.1f}"
            txt_color = (255, 120, 120) if mismatch else (200, 230, 255)
            txt = self.enemy_debug_font.render(label, True, txt_color)
            screen.blit(txt, (int(p0.x + 12), int(p0.y - 18)))

    def reset_game(self):
        """Resettaa pelin tilan ja pelaajan"""
        self._boss_storm_active = False
        self._boss_storm_next_ms = None
        self._boss_storm_hide_remaining_ms = 0
        self._boss_storm_spawn_timer_ms = 0
        self._test2_shower_cd_ms = random.randint(2200, 4200)
        self._test2_storm_phase = "idle"
        self._test2_storm_side = "top"
        self._test2_storm_timer_ms = 0
        self._test2_storm_burst_remaining = 0
        self._test2_storm_burst_step_ms = 0
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
        if self.hazard_system is not None:
            self.hazard_system.reset()
            self.meteors = self.hazard_system.meteors
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
        if self.level_number == 0 and spawn_wave_test:
            spawn_func = spawn_wave_test
        elif self.level_number == 6 and spawn_wave_test2:
            spawn_func = spawn_wave_test2
        elif self.level_number == 1:
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
        frame_start = time.perf_counter()
        self.dt = self.clock.tick(60)

        if self._refresh_view_metrics():
            self._rescale_assets_for_view()

        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F3:
                self.DEBUG_DRAW_ENEMY_FACING = not self.DEBUG_DRAW_ENEMY_FACING

        # Päivitä planeetat ja pelaaja
        planets.update_planet(self.dt)
        self.player.update(self.dt)

        if self.physics_world is not None:
            self.physics_world.step(self.dt / 1000.0)
            self.physics_metrics.update(self.physics_world.get_metrics())

        self.player.move(0,0,self.tausta_leveys,self.tausta_korkeus)
        self._update_boss_storm_phase(self.dt)
        self._update_test2_meteor_showers(self.dt)
        self._ensure_boss_bomb_hazards()

        if self.enemy_calm_timer_ms > 0:
            self.enemy_calm_timer_ms = max(0, self.enemy_calm_timer_ms - self.dt)

        # Kamera pelaajan ympärillä
        self.camera_x = max(0, min(self.player.rect.centerx - self.view_width // 2, self.tausta_leveys - self.view_width))
        self.camera_y = max(0, min(self.player.rect.centery - self.view_height // 2, self.tausta_korkeus - self.view_height))

        # Päivitä viholliset
        for e in list(self.enemies):
            e.update(self.dt, self.player, pygame.Rect(0,0,self.tausta_leveys,self.tausta_korkeus))
            shoot_dt = self.dt
            if self.enemy_calm_timer_ms > 0:
                shoot_dt = self.dt * self.enemy_calm_shoot_scale
            if isinstance(e, BossEnemy):
                e.maybe_shoot(shoot_dt, {'bullets': self.enemy_bullets, 'muzzles': self.muzzles}, player=self.player)
            else:
                e.maybe_shoot(shoot_dt, {'bullets': self.enemy_bullets, 'muzzles': self.muzzles})

        # Legacy meteor update path (non-test levels).
        if self.hazard_system is None:
            for meteor in list(self.meteors):
                meteor.update(self.dt)
                if getattr(meteor, 'dead', False):
                    self.meteors.remove(meteor)

        # Ammukset
        for bullet in list(self.player.weapons.bullets):
            hit_enemy_bullet = False

            for enemy_bullet in list(self.enemy_bullets):
                if getattr(enemy_bullet, 'state', '') == 'explode':
                    continue
                if bullet.rect.colliderect(enemy_bullet.rect):
                    if bullet in self.player.weapons.bullets:
                        self.player.weapons.bullets.remove(bullet)
                    enemy_bullet.explode()
                    if getattr(enemy_bullet, 'dead', False) and enemy_bullet in self.enemy_bullets:
                        self.enemy_bullets.remove(enemy_bullet)
                    hit_enemy_bullet = True
                    break

            if hit_enemy_bullet:
                continue

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
                                if self.hazard_system is not None:
                                    self.hazard_system.on_enemy_destroyed(enemy, is_boss=True)
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
                                    if self.hazard_system is not None:
                                        self.hazard_system.on_enemy_destroyed(enemy, is_boss=False)
                                    self.enemies.remove(enemy)
                                self.pistejarjestelma.lisaa_piste(1)
                            else:
                                self.explosion_manager.spawn_hit(impact_pos, fps=24)
                        else:
                            self.explosion_manager.spawn_enemy(impact_pos, fps=20)
                    
                            if enemy in self.enemies:
                                if self.hazard_system is not None:
                                    self.hazard_system.on_enemy_destroyed(enemy, is_boss=False)
                                self.enemies.remove(enemy)
                            self.pistejarjestelma.lisaa_piste(1)

                    break

        for b in list(self.enemy_bullets):
            b.update(self.dt, pygame.Rect(0,0,self.tausta_leveys,self.tausta_korkeus))
            if getattr(b,'dead',False):
                self.enemy_bullets.remove(b)
            elif (
                getattr(b,'state','') != 'explode'
                and b.rect.colliderect(self.player.rect)
                and self.lives > 0
                and self.player_death_menu_delay_remaining is None
            ):
                b.explode()
                if getattr(b, 'dead', False) and b in self.enemy_bullets:
                    self.enemy_bullets.remove(b)
                self.player.health = max(0, self.player.health-1)
                self.lives = self.player.health
                try:
                    if hasattr(self.player, 'trigger_hit_animation'):
                        self.player.trigger_hit_animation()
                except Exception:
                    pass

        if self.hazard_system is None:
            # Legacy meteor collision handling.
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

                        self._apply_player_knockback(direction, 360)

                        if hasattr(self.player, "collision_bounce_locked"):
                            self.player.collision_bounce_locked = True
                            self.player.collision_bounce_timer = 0.18

                        self._meteor_hit_cooldown = self.enemy_hit_cooldown_duration
                        break

            if meteor_hit_cooldown > 0:
                self._meteor_hit_cooldown = max(0, meteor_hit_cooldown - self.dt)

            # Meteors are invulnerable in non-test levels.
            for meteor in self.meteors:
                for bullet in list(self.player.weapons.bullets):
                    if bullet.rect.colliderect(meteor.rect):
                        if bullet in self.player.weapons.bullets:
                            self.player.weapons.bullets.remove(bullet)
        else:
            boss_positions = [e.rect.center for e in self.enemies if isinstance(e, BossEnemy)]
            hazard_effects = self.hazard_system.update(
                self.dt,
                self.player,
                self.player.weapons.bullets,
                boss_positions=boss_positions,
                nearby_positions=[e.rect.center for e in self.enemies],
            )

            # Placeholder for countdown beep integration.
            _countdown_tick = hazard_effects.get("countdown_tick")
            if _countdown_tick is not None:
                pass

            damage = int(hazard_effects.get("player_damage", 0))
            if damage > 0 and self.lives > 0 and self.player_death_menu_delay_remaining is None:
                self.player.health = max(0, int(self.player.health) - damage)
                self.lives = self.player.health
                try:
                    if hasattr(self.player, 'trigger_hit_animation'):
                        self.player.trigger_hit_animation()
                except Exception:
                    pass

            hp_pickups = int(hazard_effects.get("pickup_hp", 0))
            if hp_pickups > 0:
                max_hp = int(getattr(self.player, 'max_health', self.player.health))
                self.player.health = min(max_hp, int(self.player.health) + hp_pickups)
                self.lives = self.player.health

            shield_pickups = int(hazard_effects.get("pickup_shield", 0))
            if shield_pickups > 0:
                max_hp = int(getattr(self.player, 'max_health', self.player.health))
                self.player.health = min(max_hp, int(self.player.health) + shield_pickups)
                self.lives = self.player.health

            # Meteor kills use the same visual explosion style as enemy ships.
            for m_pos in hazard_effects.get("meteor_destroyed_positions", []):
                self.explosion_manager.spawn_enemy(m_pos, fps=20)

            # Test2 mode: falling meteors also sweep enemies on contact.
            if self.is_test2_level:
                for meteor in list(self.meteors):
                    for enemy in list(self.enemies):
                        if not meteor.rect.colliderect(enemy.rect):
                            continue

                        if isinstance(enemy, BossEnemy):
                            hit_cd = int(getattr(enemy, "_meteor_contact_cd_ms", 0))
                            if hit_cd > 0:
                                continue
                            enemy._meteor_contact_cd_ms = 360
                            died = enemy.take_hit(1)
                            self.explosion_manager.spawn_hit(enemy.rect.center, fps=22)
                            if died and enemy in self.enemies:
                                self.explosion_manager.spawn_boss(enemy.rect.center, fps=20)
                                if self.hazard_system is not None:
                                    self.hazard_system.on_enemy_destroyed(enemy, is_boss=True)
                                self.enemies.remove(enemy)
                                self.pistejarjestelma.lisaa_piste(5)
                        else:
                            self.explosion_manager.spawn_enemy(enemy.rect.center, fps=20)
                            if enemy in self.enemies:
                                if self.hazard_system is not None:
                                    self.hazard_system.on_enemy_destroyed(enemy, is_boss=False)
                                self.enemies.remove(enemy)
                                self.pistejarjestelma.lisaa_piste(1)

                        if meteor in self.meteors:
                            self.meteors.remove(meteor)
                            self.meteors.extend(meteor.split_children())
                        break

                for enemy in self.enemies:
                    if isinstance(enemy, BossEnemy):
                        enemy._meteor_contact_cd_ms = max(0, int(getattr(enemy, "_meteor_contact_cd_ms", 0)) - int(self.dt))

            # Shockwave ring pushes nearby entities in an outward wavefront.
            self._apply_shockwaves_from_hazards(hazard_effects.get("shockwaves", []))

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
                    self._apply_player_knockback(direction, 1000)

                # Lukitse ohjaus hetkeksi, jotta knockback ehtii näkyä
                    if hasattr(self.player, "collision_bounce_locked"):
                        self.player.collision_bounce_locked = True
                        self.player.collision_bounce_timer = 0.22
                    # estä vihollista jahtaamasta heti takaisin
                    if hasattr(enemy, "hit_player_cooldown"):
                        enemy.hit_player_cooldown = 2.5

                    # Non-boss enemies explode on collision to prevent instant chain hits.
                    if not isinstance(enemy, BossEnemy):
                        self.explosion_manager.spawn_enemy(enemy.rect.center, fps=22)
                        if enemy in self.enemies:
                            if self.hazard_system is not None:
                                self.hazard_system.on_enemy_destroyed(enemy, is_boss=False)
                            self.enemies.remove(enemy)
                            self.pistejarjestelma.lisaa_piste(1)

                    self._start_enemy_calm_period()
                    self._calm_nearby_enemies(self.player.rect.center)

                    self.enemy_hit_cooldown = self.enemy_hit_cooldown_duration
                    break
        if self.enemy_hit_cooldown > 0:
            self.enemy_hit_cooldown -= self.dt
        

        # Wave progression: wave 1 -> 2 -> 3 -> boss (4).
        # Taso 3 uses meteor hazards; they do not block wave advancement.
        meteors_cleared = len(self.meteors) == 0
        if int(self.level_number) == 3:
            meteors_cleared = True

        if (not self.is_test_level) and (not self.is_test2_level) and len(self.enemies) == 0 and meteors_cleared and not self.level_completed and self.lives > 0:
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
            try:
                with open('player_name.txt', 'r') as file:
                    self.text = file.read().strip()
            except FileNotFoundError:
                self.text = ''
            self.leaderboard.add_score(self.text,
                                       self.pistejarjestelma.hae_pisteet())
            self.leaderboard.save_to_file(os.path.join(self.base_path, 'leaderboard.json'))
            try:
                with open('player_name.txt', 'w') as file:
                    # Varmista, että tiedosto on tyhjä ennen seuraavaa peliä.
                    file.flush()
            except Exception:
                pass

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

        self.physics_metrics['frame_ms'] = (time.perf_counter() - frame_start) * 1000.0

    def draw(self, target_screen):
        """Piirrä kaikki peliobjektit annettuun ruutuun"""
        self.screen = target_screen
        if self._refresh_view_metrics():
            self._rescale_assets_for_view()
        self.screen.blit(
            self.tausta,
            (0, 0),
            area=(self.camera_x, self.camera_y, self.view_width, self.view_height),
        )

        for kuva, (x, y) in zip(self.planeetat, self.planeetta_paikat):
            self.screen.blit(kuva, (x - self.camera_x, y - self.camera_y))

        if self.hazard_system is None:
            for meteor in self.meteors:
                meteor.draw(self.screen, self.camera_x, self.camera_y)
        else:
            self.hazard_system.draw(self.screen, self.camera_x, self.camera_y)

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

        # Pisteet sijainti oikeassa yläkulmassa
        font = pygame.font.SysFont('Arial', 36)
        text = "Pisteet: " + str(self.pistejarjestelma.hae_pisteet())
        w, _ = font.size(text)
        x = self.screen.get_width() - w - 10
        self.pistejarjestelma.show_score(x, 50, font, self.screen)
        draw_hud(
            self.screen,
            self.view_width,
            self.view_height,
            self.player,
            self.lives,
            self.health_imgs,
            self.health_icon_pos,
        )
        self._draw_enemy_facing_debug(self.screen)
        self._draw_physics_overlay(self.screen)


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