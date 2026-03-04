import pygame

class Button:
    def __init__(self, x, y, width, height, text, color, text_color, screen):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.font = pygame.font.SysFont('Arial', 36)
        self.screen = screen

    def draw(self):
        pygame.draw.rect(self.screen, self.color, self.rect)
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        self.screen.blit(text_surface, text_rect)
    
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

class GameOverScreen:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont('Arial', 48)
        self.buttons = [
            Button(100, 200, 200, 50, "TRY AGAIN", (0, 255, 0), (255, 255, 255), screen),
            Button(100, 300, 200, 50, "MAIN MENU", (0, 255, 0), (255, 255, 255), screen),
            Button(100, 400, 200, 50, "QUIT", (0, 255, 0), (255, 255, 255), screen)
        ]
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            for button in self.buttons:
                if button.is_clicked(pos):
                    return button.text

    def show(self, X, Y):
        self.screen.fill((0, 0, 0))
        game_over_text = self.font.render("GAME OVER", True, (255, 0, 0))
        self.screen.blit(game_over_text, (X // 2 - game_over_text.get_width() // 2, Y // 2 - game_over_text.get_height() // 2))
        for button in self.buttons:
            button.draw()
        pygame.display.update()
    
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                handle_event = self.handle_event(event)
                if handle_event == "TRY AGAIN":
                    print("Pelaa uudelleen -painiketta painettu")
                    return "play_again"
                elif handle_event == "MAIN MENU":
                    print("Päävalikko -painiketta painettu")
                    return "main_menu"
                elif handle_event == "QUIT":
                    print("Lopeta -painiketta painettu")
                    return "quit"
        return "quit"
