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
import math
from EnemyAI import StraightEnemy, CircleEnemy
from boss_enemy import BossEnemy
from points import Points
sys.path.append(os.path.dirname(__file__))
from Player import Player
from MainMenu import MainMenu
from SpriteSettings import SpriteSettings
from itertools import product


# Näytä päävalikko ensin
pygame.init()
menu = MainMenu()
result = menu.run()

# Jos käyttäjä valitsi QUIT, lopeta
if result != "start_game":
    pygame.quit()
    sys.exit()

currentWorkDir = os.getcwd()
print(currentWorkDir)

sourceFileDir = os.path.dirname(os.path.abspath(__file__))
print(sourceFileDir)


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

# load, convert and scale background to window size
tausta = pygame.image.load(os.path.join(os.path.dirname(__file__),'images','taustat','avaruus.png')).convert()
tausta = pygame.transform.scale(tausta, (X, Y))
# Käytetään hallittua skaalausta (esim. 1.5x) jotta tausta on hieman suurempi kuin ikkuna
scale_factor = 1
tausta = pygame.transform.scale(tausta, (int(X * scale_factor), int(Y * scale_factor)))

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
# BOSS kuva
boss_image = pygame.transform.scale(
    pygame.image.load(os.path.join(viholliset_path, "12.png")).convert_alpha(),
    (320, 320)  # iso boss
)

# Load Ship sprites (Ship2 by default) and exhaust/shot frames
ss = SpriteSettings(base_path=os.path.join(os.path.dirname(__file__), 'enemy-sprite'), ship='Ship2')
ss.load_all()



world_rect = pygame.Rect(0, 0, tausta_leveys, tausta_korkeus)

# Collision and UI helpers moved to modules for modularity
USE_SPATIAL_COLLISIONS = True
from collisions import SpatialHash, apply_impact, separate, _get_pos
from ui import draw_hud, draw_death_overlay
from ui import init_enemy_health_bars, get_enemy_bar_images, draw_healthbar_custom
import planets

# Instantiate spatial hash and collision state
spatial_hash = SpatialHash()
collisions = set()

enemies = []
enemy_bullets = []
muzzles = []
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
enemies.append(e1)

e2 = CircleEnemy(img1, tausta_leveys // 2 + 300, tausta_korkeus // 2, radius=180, angular_speed=1)
e2.exhaust_turbo = exhaust_turbo
e2.exhaust_normal = exhaust_normal
e2.shots = shot_frames
enemies.append(e2)


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
# - Corvette-sprite-kansion kaikki .png-kehykset
# - Player-olio maailman keskelle
# -----------------------------


# Lataa liikeanimaation kehykset: ProjektiProto/img/Corvette/Move
corvette_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), 'alukset','alus', 'Corvette', 'Move'))
frames = []
if os.path.isdir(corvette_dir):
    for f in sorted(os.listdir(corvette_dir)):
        if f.lower().endswith('.png'):
            frames.append(pygame.image.load(os.path.join(corvette_dir, f)).convert_alpha())


# Lataa boost-animaatiokehykset (näytetään kun W painetaan)
boost_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), 'alukset','alus', 'Corvette', 'Boost'))
boost_frames = []
if os.path.isdir(boost_dir):
    for f in sorted(os.listdir(boost_dir)):
        if f.lower().endswith('.png'):
            boost_frames.append(pygame.image.load(os.path.join(boost_dir, f)).convert_alpha())

# Luodaan pistelaskuriolio.
pistejarjestelma = Points()

# Luo pelaaja maailman keskelle
player_start_x = tausta_leveys // 2
player_start_y = tausta_korkeus // 2
player_scale_multiplier = 10
player_scale_factor = 0.5  # Skaalaa pelaaja puoleen kokoon
player = Player(player_scale_factor, frames, player_start_x, player_start_y, boost_frames=boost_frames, max_health=5)

# Pelaajan elämät / health
lives = player.health if hasattr(player, 'health') else 5
enemy_hit_cooldown = 0
enemy_hit_cooldown_duration = 1000  # 1 sekunti (millisekuntia)
death_menu = False

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

# Alusta kamera ennen silmukkaa
camera_x = 0
camera_y = 0
run = True
pause = False

# BOSS ilmestyy pisteiden mukaan
boss_spawned = False
BOSS_TRIGGER_SCORE = 2

while run:
    # Tapahtumien käsittely
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pause = True
    # rajoita framerate ja hae dt (millisekunteina)
    dt = clock.tick(60)
    try:
        planets.update_planet(dt)
    except Exception:
        pass

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
        
    # Piirrä viholliset
    for e in enemies:
            e.update(dt, player, world_rect)
            # enemies may auto-shoot; bullets and muzzle animations appended to lists
            try:
                # BossEnemy supports targeting player for homing missiles
                if isinstance(e, BossEnemy):
                    e.maybe_shoot(dt, {'bullets': enemy_bullets, 'muzzles': muzzles}, player=player)
                else:
                    e.maybe_shoot(dt, {'bullets': enemy_bullets, 'muzzles': muzzles})
            except Exception:
                pass

    # Draw boss health bars in the left margin of the canvas (stacked)
    bosses = [be for be in enemies if isinstance(be, BossEnemy)]
    for idx, e in enumerate(bosses):
        try:
            # Simple explicit sizes and positions for fill and frame
            margin = 16
            fill_w, fill_h = 20, 40
            frame_w, frame_h = 340, 56
            frame_x = margin
            frame_y = margin + idx * (frame_h + 8)
            # center fill inside frame
            fill_x = frame_x + (frame_w - fill_w) // 2
            fill_y = frame_y + (frame_h - fill_h) // 2

            cur_hp = getattr(e, 'hp', getattr(e, 'health', getattr(e, 'HP', 0)))
            max_hp = getattr(e, 'max_hp', getattr(e, 'max_health', getattr(e, 'HP_MAX', cur_hp)))

            imgs = get_enemy_bar_images()
            draw_healthbar_custom(screen,
                                  fill_w, fill_h,
                                  fill_x, fill_y,
                                  frame_w, frame_h,
                                  frame_x, frame_y,
                                  cur_hp, max_hp,
                                  imgs=imgs,
                                  tint=(255,40,40))
        except Exception:
            pass

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
                    minsep = (getattr(a, 'radius', max(a.rect.width, a.rect.height) * 0.5) +
                             getattr(b, 'radius', max(b.rect.width, b.rect.height) * 0.5))
                    if pa.distance_squared_to(pb) < (minsep * minsep):
                        # canonical pair ordering
                        pair = (a, b) if id(a) < id(b) else (b, a)
                        if pair not in prev_collisions:
                            apply_impact(*pair)
                        collisions.add(pair)

            # separate with a few iterations for stability
            for _ in range(8):
                collisions = {(a, b) for (a, b) in collisions if not separate(a, b)}
                if not collisions:
                    break
        except Exception:
            # fail safe: continue without spatial collisions
            collisions = set()

    # Tarkista osumat pelaajaammuksien ja vihollisten välillä
    for bullet in list(player.weapons.bullets):
        for enemy in list(enemies):
            if bullet.rect.colliderect(enemy.rect):
                # Remove player's bullet
                if bullet in player.weapons.bullets:
                    player.weapons.bullets.remove(bullet)

                # Spawn explosion animation at enemy position (use shot_frames explode if available)
                explode_list = shot_frames.get('explode') if isinstance(shot_frames, dict) else None
                if explode_list:
                    from EnemyHelpers import EnemyBullet
                    exp = EnemyBullet(pygame.Vector2(enemy.rect.center), pygame.Vector2(0, 0),
                                      start_frames=None, flight_frames=None, explode_frames=explode_list, speed=0)
                    exp.explode()
                    enemy_bullets.append(exp)

                # Boss takes multiple hits
                if isinstance(enemy, BossEnemy):
                    died = enemy.take_hit(1)
                    if died:
                        enemies.remove(enemy)
                        pistejarjestelma.lisaa_piste(5)  # boss-bonus
                else:
                    # Normal enemy dies immediately
                    enemies.remove(enemy)
                    pistejarjestelma.lisaa_piste(1)

                break  # move to next player bullet

    # Bossen ilmestyminen
    if (not boss_spawned) and pistejarjestelma.hae_pisteet() >= BOSS_TRIGGER_SCORE:
        boss_spawned = True

        boss = BossEnemy(
            boss_image,
            world_rect,
            hp=100,
            enter_speed=280,
            move_speed=320
    )

        # give boss shot frames so it can spawn animated/homing bullets
        boss.shots = shot_frames
        enemies.append(boss)

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
                    p_radius = max(player.rect.width, player.rect.height) * 0.5
                except Exception:
                    p_radius = max(player.rect.width, player.rect.height) * 0.5
                try:
                    e_radius = max(enemy.rect.width, enemy.rect.height) * 0.5
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

                # Deduct life (prefer player's health) and start cooldown
                try:
                    if hasattr(player, 'health'):
                        player.health = max(0, int(player.health) - 1)
                        lives = player.health
                    else:
                        lives -= 1
                except Exception:
                    lives -= 1
                enemy_hit_cooldown = enemy_hit_cooldown_duration
                break  # only one collision event per cooldown

    # Päivitä cooldown
    if enemy_hit_cooldown > 0:
        enemy_hit_cooldown -= dt

    # Tarkista pelin loppu -> näytä death menu instead of immediate quit
    if lives <= 0:
        death_menu = True

    for e in enemies:
        e.draw(screen, camera_x, camera_y)

    # Muzzle (paikka mistä ammus lähtee vihollisesta)
    for m in list(muzzles):
        try:
            m.update(dt)
            if getattr(m, 'dead', False):
                muzzles.remove(m)
                continue
            m.draw(screen, camera_x, camera_y)
        except Exception:
            try:
                muzzles.remove(m)
            except Exception:
                pass

    #Päivitä osumat ja tee räjähdysanimaatio.
    for b in list(enemy_bullets):
        b.update(dt, world_rect)
        if getattr(b, 'dead', False):
            try:
                enemy_bullets.remove(b)
            except ValueError:
                pass
            continue
        # törmäys pelaajaan. Trigger räjähdys ja poista ammus. Pelaaja menettää elämän.
        if getattr(b, 'state', '') == 'flight' and b.rect.colliderect(player.rect):
            # trigger explosion at bullet position and stop its movement
            try:
                b.explode()
            except Exception:
                # fallback: remove and decrement
                try:
                    enemy_bullets.remove(b)
                except ValueError:
                    pass
            # decrement player's health if available, else decrement lives
            try:
                if hasattr(player, 'health'):
                    player.health = max(0, int(player.health) - 1)
                    lives = player.health
                else:
                    lives -= 1
            except Exception:
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

    # Death overlay (Restart / Quit)
    if death_menu:
        overlay = pygame.Surface((X, Y))
        overlay.set_alpha(220)
        overlay.fill((10, 10, 10))
        screen.blit(overlay, (0, 0))

        font_large = pygame.font.SysFont('Arial', 48)
        font_small = pygame.font.SysFont('Arial', 28)
        title = font_large.render("", True, (220, 80, 80))
        # center the title and buttons using the actual screen rect
        screen_rect = screen.get_rect()
        cx, cy = screen_rect.center
        title_rect = title.get_rect(center=(cx, cy - 100))
        screen.blit(title, title_rect.topleft)

        btn_w, btn_h = 320, 64
        restart_btn = pygame.Rect(0, 0, btn_w, btn_h)
        quit_btn = pygame.Rect(0, 0, btn_w, btn_h)
        restart_btn.center = (cx, cy)
        quit_btn.center = (cx, cy + btn_h + 16)

        pygame.draw.rect(screen, (70, 150, 70), restart_btn)
        pygame.draw.rect(screen, (150, 70, 70), quit_btn)

        # draw button labels centered
        restart_label = font_small.render("Restart", True, (255, 255, 255))
        quit_label = font_small.render("Quit", True, (255, 255, 255))
        screen.blit(restart_label, restart_label.get_rect(center=restart_btn.center).topleft)
        screen.blit(quit_label, quit_label.get_rect(center=quit_btn.center).topleft)

        pygame.display.update()

        # modal loop for death menu
        in_death = True
        while in_death:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    mx, my = ev.pos
                    if restart_btn.collidepoint(mx, my):
                        # reset player health and position, clear enemies and reset cooldown
                        try:
                            player.health = int(getattr(player, 'max_health', 5))
                            lives = player.health
                        except Exception:
                            lives = 5
                        try:
                            player.pos = pygame.Vector2(player_start_x, player_start_y)
                            player.rect.center = (int(player.pos.x), int(player.pos.y))
                            player.vel = pygame.Vector2(0, 0)
                        except Exception:
                            pass
                        # recreate simple enemies
                        enemies.clear()
                        try:
                            ne1 = StraightEnemy(img0, 200, 200, speed=220)
                            ne1.exhaust_turbo = exhaust_turbo
                            ne1.exhaust_normal = exhaust_normal
                            ne1.shots = shot_frames
                            enemies.append(ne1)
                            ne2 = CircleEnemy(img1, tausta_leveys // 2 + 300, tausta_korkeus // 2, radius=180, angular_speed=2.2)
                            ne2.exhaust_turbo = exhaust_turbo
                            ne2.exhaust_normal = exhaust_normal
                            ne2.shots = shot_frames
                            enemies.append(ne2)
                        except Exception:
                            pass
                        enemy_hit_cooldown = 0
                        death_menu = False
                        in_death = False
                        break
                    elif quit_btn.collidepoint(mx, my):
                        pygame.quit()
                        sys.exit()
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
        continue  # skip normal frame logic while death menu handled

    # Pause overlay
    if pause:
        overlay = pygame.Surface((X, Y))
        overlay.set_alpha(180)
        overlay.fill((30, 30, 30))
        screen.blit(overlay, (0, 0))

        font = pygame.font.SysFont('Arial', 48)
        pause_text = font.render("PAUSE", True, (255, 255, 255))
        screen.blit(pause_text, (X // 2 - 100, Y // 2 - 150))

        button_font = pygame.font.SysFont('Arial', 36)
        continue_btn = pygame.Rect(X // 2 - 120, Y // 2 - 50, 240, 60)
        quit_btn = pygame.Rect(X // 2 - 120, Y // 2 + 30, 240, 60)
        settings_btn = pygame.Rect(X // 2 - 120, Y // 2 + 110, 240, 60)

        pygame.draw.rect(screen, (70, 150, 70), continue_btn)
        pygame.draw.rect(screen, (150, 70, 70), quit_btn)
        pygame.draw.rect(screen, (70, 70, 150), settings_btn)

        screen.blit(button_font.render("Continue", True, (255,255,255)), (continue_btn.x+40, continue_btn.y+10))
        screen.blit(button_font.render("Quit", True, (255,255,255)), (quit_btn.x+80, quit_btn.y+10))
        screen.blit(button_font.render("Settings", True, (255,255,255)), (settings_btn.x+60, settings_btn.y+10))

        pygame.display.update()

        # Pause-tapahtumien käsittely
        paused = True
        while paused:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                    paused = False
                    pause = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    if continue_btn.collidepoint(mx, my):
                        pause = False
                        paused = False
                    elif quit_btn.collidepoint(mx, my):
                        run = False
                        paused = False
                        pause = False
                    elif settings_btn.collidepoint(mx, my):
                        # Avaa settings-näkymä tähän
                        pass
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pause = False
                        paused = False
        continue  # Älä suorita muuta pelisilmukkaa kun pause päällä
    # Päivitä näyttö
    pygame.display.update()
    

pygame.quit()