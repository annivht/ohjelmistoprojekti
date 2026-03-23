import pygame
from Valikot.menu_style import MenuButton, draw_dim_overlay, draw_menu_panel

class GameOverScreen:
    def __init__(self, screen):
        self.screen = screen
        panel_width = 760
        panel_height = 560
        screen_w, screen_h = self.screen.get_size()
        self.panel_rect = pygame.Rect(
            screen_w // 2 - panel_width // 2,
            screen_h // 2 - panel_height // 2,
            panel_width,
            panel_height,
        )
        button_width = 300
        button_height = 78
        button_spacing = 22
        total_height = 3 * button_height + 2 * button_spacing
        start_y = self.panel_rect.top + 200 + (self.panel_rect.height - 270 - total_height) // 2
        center_x = screen_w // 2 - button_width // 2
        self.buttons = [
            MenuButton(center_x, start_y, button_width, button_height, "TRY AGAIN", action="TRY AGAIN", variant="success"),
            MenuButton(center_x, start_y + button_height + button_spacing, button_width, button_height, "MAIN MENU", action="MAIN MENU"),
            MenuButton(center_x, start_y + 2 * (button_height + button_spacing), button_width, button_height, "QUIT", action="QUIT", variant="danger"),
        ]
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            for button in self.buttons:
                if button.is_clicked(pos):
                    return button.action

    def show(self, X, Y, overlay=True, background_surface=None):
        """
        Piirtää Game Over -näytön.

        Muutos (tämän patchin vuoksi): oletuksena käytetään läpikuultavaa overlay-tilaa
        (`overlay=True`) jolloin taustalla pyörivät animaatiot pysyvät näkyvissä.
        Jos halutaan alkuperäinen, koko ruudun tyhjentävä käytös, kutsu
        `show(X, Y, overlay=False)`.
        """
        if background_surface is not None:
            try:
                self.screen.blit(background_surface, (0, 0))
            except Exception:
                self.screen.fill((0, 0, 0))
        if overlay:
            # Piirretään läpikuultava musta pinta päälle (ei tyhjennetä taustaa)
            draw_dim_overlay(self.screen)
        else:
            # Takautuva toiminta: joko tyhjennetään näyttö kuten ennen
            self.screen.fill((0, 0, 0))

        draw_menu_panel(self.screen, self.panel_rect, "GAME OVER", "Your mission ended")
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.update(mouse_pos)
            button.draw(self.screen)
        pygame.display.update()
    
    def run(self):
        """
        Säilytetään takautuva, blokkaava `run()`-metodi, mutta huomioi että
        tätä kutsuttaessa pääsilmukka pysähtyy (ja pelin logiikka/animoinnit
        yleensä jäävät odottamaan). Suositus: älä kutsu `run()` heti kun pelaaja
        kuolee, vaan anna pelin pääsilmukan toistaa tuhoutumisanimointi ja
        kutsu `show()` (oletuksena overlay) tai käsittele tapahtumat pääsilmukassa.
        """
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                result = self.handle_event(event)
                if result == "TRY AGAIN":
                    print("Pelaa uudelleen -painiketta painettu")
                    return "play_again"
                elif result == "MAIN MENU":
                    print("Päävalikko -painiketta painettu")
                    return "main_menu"
                elif result == "QUIT":
                    print("Lopeta -painiketta painettu")
                    return "quit"
        return "quit"
