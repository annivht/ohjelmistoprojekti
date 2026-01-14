import pygame
from pygame.locals import QUIT
import sys
import os


#peli-ikkunan leveys ja korkeus
WIDTH, HEIGHT = 1200, 800

# Pelin kuvamateriaalit
img_maa = pygame.image.load('images/taustat/background_imageDarkGround.jpg')
img_tahti = pygame.image.load('images/taustat/SpaceStars_oma.jpg')
img_alus = pygame.image.load('images/alukset/4.png')
img_start = pygame.image.load('images/elementit/14.png')




def paivita_aluksen_paikka(keys, alus_x, alus_y, alus_nopeus, alus_w, alus_h, screen_w, screen_h):
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        alus_x -= alus_nopeus
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        alus_x += alus_nopeus
    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        alus_y += alus_nopeus
    if keys[pygame.K_UP] or keys[pygame.K_w]:
        alus_y -= alus_nopeus
    alus_x = max(0, min(alus_x, screen_w - alus_w))
    alus_y = max(0, min(alus_y, screen_h - alus_h))
    return alus_x, alus_y


def piirra_alus(win, img_alus, alus_x, alus_y):
    win.blit(img_alus, (int(alus_x), int(alus_y)))


def piirra_start(win, img_start):
    sx = (WIDTH - img_start.get_width()) // 2
    sy = (HEIGHT - img_start.get_height()) // 2
    win.blit(img_start, (sx, sy))


def pistejarjestelma():
    pass


def ammukset():
    pass

def gameOver():
    pass


class AnimatedSprite(pygame.sprite.Sprite):
    pass



def main():
    pygame.init()
    win = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    global img_maa, img_tahti, img_alus, img_start
    SHIP_W, SHIP_H = 64, 64
    START_W, START_H = 200, 100
    # Skaalataan taustakuvat vasta kun ikkuna on alustettu
    img_maa = pygame.transform.scale(img_maa, win.get_size())
    img_tahti = pygame.transform.scale(img_tahti, win.get_size())
    # Convert_alpha vaatii alustetun displayn -> tehdään sen jälkeen
    img_alus = img_alus.convert_alpha()
    img_start = img_start.convert_alpha()
    # Alus ja start skaalataan
    img_alus = pygame.transform.scale(img_alus, (SHIP_W, SHIP_H))
    img_start = pygame.transform.scale(img_start, (START_W, START_H))
    alus_x = (WIDTH- SHIP_W) // 2
    alus_y = HEIGHT - SHIP_H - 20
    alus_nopeus = 8
    speed = 1.5
    maa_y = 0.0
    star_y = 0.0

    
    show_maa = True
    start_screen = True

    # Try to load animated frames from a sprite-sheet. If it fails, we'll
    # fall back to the static `img_alus` already loaded above.
    player_sprite = None
    animated_group = None


    running = True
    while running:
        clock.tick(30)
        for ev in pygame.event.get():
            if ev.type == QUIT:
                running = False
            if start_screen:
                if ev.type == pygame.KEYDOWN and (ev.key == pygame.K_SPACE or ev.key == pygame.K_RETURN):
                    start_screen = False
                if ev.type == pygame.MOUSEBUTTONDOWN:
                    start_screen = False
        if not running:
            break
        win.fill((0, 0, 0))
        # päivitetään taustojen offsetit ja piirretään ne (yksinkertaisemmin inline)
        star_y += speed
        star_y %= HEIGHT
        win.blit(img_tahti, (0, int(star_y)))
        win.blit(img_tahti, (0, int(star_y) - HEIGHT))
        if show_maa:
            maa_y += speed
            win.blit(img_maa, (0, int(maa_y)))
            if maa_y >= HEIGHT:
                show_maa = False
        if start_screen:
            piirra_start(win, img_start)
            pygame.display.update()
            continue
        keys = pygame.key.get_pressed()
        alus_x, alus_y = paivita_aluksen_paikka(keys, alus_x, alus_y, alus_nopeus, SHIP_W, SHIP_H, WIDTH, HEIGHT)
        # Determine whether the player is moving (any movement key pressed)
        moving = (
            keys[pygame.K_LEFT] or keys[pygame.K_a] or
            keys[pygame.K_RIGHT] or keys[pygame.K_d] or
            keys[pygame.K_UP] or keys[pygame.K_w] or
            keys[pygame.K_DOWN] or keys[pygame.K_s]
        )
        # Draw either animated sprite or fallback static image
        piirra_alus(win, img_alus, alus_x, alus_y)
        pygame.display.update()
    pygame.quit()


if __name__ == '__main__':
    main()