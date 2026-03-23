import pygame
from Valikot.menu_style import MenuButton, draw_dim_overlay, draw_menu_panel

# Näytön asetukset
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 800

DARK_BLUE = (52, 78, 91)


class NextLevel:
	"""Seuraavan tason valikon hallinta"""

	def __init__(self, current_level=1, max_level=None, display_current_level=None, display_next_level=None, screen=None, background_surface=None):
		if not pygame.get_init():
			pygame.init()
		if not pygame.display.get_init():
			pygame.display.init()

		self.uses_external_screen = screen is not None
		if self.uses_external_screen:
			self.screen = screen
		else:
			self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
			pygame.display.set_caption("Rocket Game - Next Level")

		self.background_surface = background_surface
		panel_width = 760
		panel_height = 560
		self.panel_rect = pygame.Rect(
			SCREEN_WIDTH // 2 - panel_width // 2,
			SCREEN_HEIGHT // 2 - panel_height // 2,
			panel_width,
			panel_height,
		)

		self.current_level = int(current_level)
		self.max_level = max_level
		self.next_level = self.current_level + 1
		self.display_current_level = self.current_level if display_current_level is None else int(display_current_level)
		self.display_next_level = self.next_level if display_next_level is None else int(display_next_level)

		button_width = 300
		button_height = 78
		button_spacing = 22
		total_height = 3 * button_height + 2 * button_spacing
		start_y = self.panel_rect.top + 220 + (self.panel_rect.height - 290 - total_height) // 2
		center_x = SCREEN_WIDTH // 2 - button_width // 2

		self.buttons = [
			MenuButton(center_x, start_y, button_width, button_height, "NEXT LEVEL", action="next_level", variant="success"),
			MenuButton(center_x, start_y + button_height + button_spacing, button_width, button_height, "SETTINGS", action="settings"),
			MenuButton(center_x, start_y + 2 * (button_height + button_spacing), button_width, button_height, "QUIT", action="quit", variant="danger"),
		]
		self.clock = pygame.time.Clock()
		self.running = True

	def handle_events_from(self, events):
		for event in events:
			if event.type == pygame.QUIT:
				self.running = False

			if event.type == pygame.MOUSEBUTTONDOWN:
				mouse_pos = pygame.mouse.get_pos()
				for button in self.buttons:
					if button.is_clicked(mouse_pos):
						return button.action

		return None

	def handle_events(self):
		return self.handle_events_from(pygame.event.get())

	def resolve_action(self, action):
		if action == "next_level":
			if self.max_level is not None and self.next_level > self.max_level:
				return "game_completed"
			return self.next_level
		if action == "settings":
			return "settings"
		if action == "quit":
			return "quit"
		return None

	def draw(self, surface=None):
		target = self.screen if surface is None else surface
		if self.background_surface is not None:
			try:
				target.blit(self.background_surface, (0, 0))
			except Exception:
				target.fill(DARK_BLUE)
		else:
			target.fill(DARK_BLUE)

		draw_dim_overlay(target)
		draw_menu_panel(
			target,
			self.panel_rect,
			"LEVEL COMPLETE",
			f"Current: {self.display_current_level}   Next: {self.display_next_level}",
		)

		mouse_pos = pygame.mouse.get_pos()
		for button in self.buttons:
			button.update(mouse_pos)
			button.draw(target)

		if surface is None:
			pygame.display.update()

	def run(self):
		while self.running:
			result = self.resolve_action(self.handle_events())
			if result is not None:
				return result

			self.draw()
			self.clock.tick(60)

		return "quit"

