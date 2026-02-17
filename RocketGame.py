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

e2 = CircleEnemy(img1, tausta_leveys // 2 + 300, tausta_korkeus // 2, radius=180, angular_speed=2.2)
e2.exhaust_turbo = exhaust_turbo
e2.exhaust_normal = exhaust_normal
e2.shots = shot_frames
enemies.append(e2)


planeetta_paikat = []
for _ in range(len(planeetat)):
    x = random.randint(0, max(0, tausta_leveys - 300))
    y = random.randint(0, max(0, tausta_korkeus - 300))
    planeetta_paikat.append((x, y))



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
player = Player(player_scale_factor, frames, player_start_x, player_start_y, boost_frames=boost_frames)

# Pelaajan elämät
lives = 3
enemy_hit_cooldown = 0
enemy_hit_cooldown_duration = 1000  # 1 sekunti (millisekuntia)

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

                # Push both entities apart so they "bounce" away from each other.
                # Use a separation distance based on sprite sizes to avoid immediate re-collision.
                separation = max(16, (player.rect.width + enemy.rect.width) * 0.25)
                try:
                    player.pos += normal * separation
                    player.rect.center = (int(player.pos.x), int(player.pos.y))
                except Exception:
                    # fallback to rect-only position adjustments
                    player.rect.centerx += int(normal.x * separation)
                    player.rect.centery += int(normal.y * separation)

                try:
                    if hasattr(enemy, 'pos'):
                        enemy.pos -= normal * separation
                        enemy.rect.center = (int(enemy.pos.x), int(enemy.pos.y))
                    else:
                        enemy.rect.centerx -= int(normal.x * separation)
                        enemy.rect.centery -= int(normal.y * separation)
                except Exception:
                    pass

                # Mass-based impulse along collision normal (1D impulse resolution)
                # Ensure both entities have velocity vectors
                p_vel = getattr(player, 'vel', None)
                if p_vel is None:
                    try:
                        player.vel = pygame.Vector2(0, 0)
                        p_vel = player.vel
                    except Exception:
                        p_vel = pygame.Vector2(0, 0)

                e_vel = getattr(enemy, 'vel', None)
                if e_vel is None:
                    try:
                        enemy.vel = pygame.Vector2(0, 0)
                        e_vel = enemy.vel
                    except Exception:
                        e_vel = pygame.Vector2(0, 0)

                # masses (defaults)
                m1 = float(getattr(player, 'mass', 1.0))
                m2 = float(getattr(enemy, 'mass', 1.0))

                # relative velocity along normal
                v_rel = p_vel - e_vel
                vel_along_normal = v_rel.dot(normal)

                # restitution (bounciness)
                restitution = 0.5

                # If velocities are separating already, still apply a small corrective impulse to push apart
                # Compute impulse scalar j
                denom = (1.0 / m1) + (1.0 / m2)
                j = 0.0
                # Use negative vel_along_normal (approach) or, if zero/positive, apply a corrective nudge
                if vel_along_normal < 0:
                    j = -(1.0 + restitution) * vel_along_normal / denom
                else:
                    # small separation impulse proportional to overlap/separation distance
                    j = (max(8.0, separation) * 0.5) / denom

                # clamp impulse to avoid extreme values
                j = max(min(j, 2000.0), -2000.0)

                # apply impulse
                try:
                    player.vel = pygame.Vector2(p_vel + (j * normal) / m1)
                except Exception:
                    try:
                        player.vel = pygame.Vector2((j * normal) / m1)
                    except Exception:
                        pass

                try:
                    if hasattr(enemy, 'vel'):
                        enemy.vel = pygame.Vector2(e_vel - (j * normal) / m2)
                    else:
                        # fallback: nudge circular enemies' angle
                        if hasattr(enemy, 'angle'):
                            enemy.angle += math.pi * 0.5
                except Exception:
                    pass

                # Deduct life and start cooldown
                lives -= 1
                enemy_hit_cooldown = enemy_hit_cooldown_duration
                break  # only one collision event per cooldown

    # Päivitä cooldown
    if enemy_hit_cooldown > 0:
        enemy_hit_cooldown -= dt

    # Tarkista pelin loppu
    if lives <= 0:
        run = False

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
            lives -= 1
            continue

    # Vihollisen ammuksen piirtoa
    for b in enemy_bullets:
        b.draw(screen, camera_x, camera_y)


    # Piirrä pelaaja kameran suhteessa
    player.draw(screen, camera_x, camera_y)

    # Näytä pisteet vasemmassa yläkulmassa.
    pistejarjestelma.show_score(10, 10, pygame.font.SysFont('Arial', 24), screen)

    # Näytä elämät oikeassa yläkulmassa
    font = pygame.font.SysFont('Arial', 24)
    lives_text = font.render(f"Elämät: {lives}", True, (255, 255, 255))
    screen.blit(lives_text, (X - 200, 10))

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