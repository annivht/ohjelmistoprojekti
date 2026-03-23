import pygame

TEXT_COLOR = (240, 247, 255)
SUBTEXT_COLOR = (188, 211, 236)

OVERLAY_RGBA = (6, 14, 24, 155)
PANEL_RGBA = (20, 44, 68, 195)
PANEL_BORDER_COLOR = (134, 192, 244)

BUTTON_FILL = (56, 119, 178)
BUTTON_HOVER = (86, 149, 212)
BUTTON_BORDER = (225, 239, 255)

BUTTON_DANGER_FILL = (153, 65, 68)
BUTTON_DANGER_HOVER = (188, 84, 88)

BUTTON_SUCCESS_FILL = (62, 142, 92)
BUTTON_SUCCESS_HOVER = (91, 172, 120)

_title_font = None
_button_font = None
_small_font = None


def ensure_fonts():
    global _title_font, _button_font, _small_font

    if not pygame.font.get_init():
        pygame.font.init()

    if _title_font is None:
        _title_font = pygame.font.Font(None, 80)
    if _button_font is None:
        _button_font = pygame.font.Font(None, 46)
    if _small_font is None:
        _small_font = pygame.font.Font(None, 34)



def get_fonts():
    ensure_fonts()
    return _title_font, _button_font, _small_font



def draw_dim_overlay(surface, alpha_rgba=OVERLAY_RGBA):
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill(alpha_rgba)
    surface.blit(overlay, (0, 0))



def draw_menu_panel(surface, panel_rect, title_text, subtitle_text=None):
    title_font, _, small_font = get_fonts()

    panel_surface = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(
        panel_surface,
        PANEL_RGBA,
        panel_surface.get_rect(),
        border_radius=24,
    )
    pygame.draw.rect(
        panel_surface,
        PANEL_BORDER_COLOR,
        panel_surface.get_rect(),
        width=3,
        border_radius=24,
    )
    surface.blit(panel_surface, panel_rect.topleft)

    title_surface = title_font.render(title_text, True, TEXT_COLOR)
    title_rect = title_surface.get_rect(center=(panel_rect.centerx, panel_rect.top + 64))
    surface.blit(title_surface, title_rect)

    if subtitle_text:
        subtitle_surface = small_font.render(subtitle_text, True, SUBTEXT_COLOR)
        subtitle_rect = subtitle_surface.get_rect(center=(panel_rect.centerx, panel_rect.top + 114))
        surface.blit(subtitle_surface, subtitle_rect)


class MenuButton:
    def __init__(self, x, y, width, height, text, action=None, variant="primary"):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.variant = variant
        self.is_hovered = False

    def _colors(self):
        if self.variant == "danger":
            fill = BUTTON_DANGER_HOVER if self.is_hovered else BUTTON_DANGER_FILL
            return fill, BUTTON_BORDER

        if self.variant == "success":
            fill = BUTTON_SUCCESS_HOVER if self.is_hovered else BUTTON_SUCCESS_FILL
            return fill, BUTTON_BORDER

        fill = BUTTON_HOVER if self.is_hovered else BUTTON_FILL
        return fill, BUTTON_BORDER

    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

    def draw(self, surface):
        _, button_font, _ = get_fonts()
        fill_color, border_color = self._colors()

        pygame.draw.rect(surface, fill_color, self.rect, border_radius=12)
        pygame.draw.rect(surface, border_color, self.rect, width=3, border_radius=12)

        text_surface = button_font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
