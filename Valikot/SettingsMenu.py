import pygame

from physics_settings import (
    DEFAULT_PHYSICS_SETTINGS,
    get_physics_preset,
    load_physics_presets,
    load_physics_settings,
    save_physics_preset,
    save_physics_settings,
)

#------------------------------------------------------
#Asennus: pip install pygame-menu
#------------------------------------------------------


# Oletusnayton asetukset (kaytetaan vain koordinaatteihin, ei luoda uutta ikkunaa)
WIDTH, HEIGHT = 700, 600

# Standard RGB colors
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
CYAN = (0, 100, 100)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


def main():
    try:
        import pygame_menu as pm
    except Exception:
        pm = None

    if pm is None:
        _fallback_settings_screen()
        return

    screen = pygame.display.get_surface()
    if screen is None:
        screen = pygame.display.set_mode((1600, 800))

    # Pause-style translucent backdrop: frozen frame + dark alpha overlay.
    frozen_bg = screen.copy()
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 128))

    def draw_translucent_bg():
        screen.blit(frozen_bg, (0, 0))
        screen.blit(overlay, (0, 0))

    physics_data = load_physics_settings()
    preset_selector = None

    graphics = [
        ("Low", "low"),
        ("Medium", "medium"),
        ("High", "high"),
        ("Ultra High", "ultra high"),
    ]

    resolution = [
        ("1920x1080", "1920x1080"),
        ("1920x1200", "1920x1200"),
        ("1280x720", "1280x720"),
        ("2560x1440", "2560x1440"),
        ("3840x2160", "3840x2160"),
    ]

    difficulty = [
        ("Easy", "Easy"),
        ("Medium", "Medium"),
        ("Expert", "Expert"),
    ]

    perspectives = [
        ("FPP", "fpp"),
        ("TPP", "tpp"),
    ]

    physics_profiles = [
        ("Realistic", "realistic"),
        ("Balanced", "balanced"),
        ("Arcade", "arcade"),
    ]

    def _profile_index(value):
        value = str(value).strip().lower()
        for i, (_, profile_value) in enumerate(physics_profiles):
            if profile_value == value:
                return i
        return 1

    def _current_physics_from_menu():
        data = physics_menu.get_input_data()
        profile_value = data.get("physics_profile", (("Balanced", "balanced"), 1))[0][1]
        offset_value = float(data.get("physics_offset", 0.0))
        speed_value = float(data.get("physics_speed", 1.0))
        turn_value = float(data.get("physics_turn", 1.0))
        return {
            "physics_profile": profile_value,
            "sprite_angle_offset_deg": offset_value,
            "speed_multiplier": speed_value,
            "turn_multiplier": turn_value,
        }

    def save_physics_from_menu():
        save_physics_settings(_current_physics_from_menu())

    def save_preset_from_menu():
        nonlocal preset_selector
        data = physics_menu.get_input_data()
        preset_name = str(data.get("physics_preset_name", "")).strip()
        if not preset_name:
            print("Preset name is empty; preset not saved.")
            return

        try:
            save_physics_preset(preset_name, _current_physics_from_menu())
            print(f"Saved physics preset: {preset_name}")
            if preset_selector is not None:
                items = [(name, name) for name in load_physics_presets().keys()] or [("None", "")]
                try:
                    preset_selector.update_items(items)
                except Exception:
                    pass
        except Exception as exc:
            print(f"Could not save preset '{preset_name}': {exc}")

    def load_selected_preset_from_menu():
        data = physics_menu.get_input_data()
        selected_name = str(data.get("physics_preset_select", (("None", ""), 0))[0][1]).strip()
        if not selected_name:
            print("No preset selected.")
            return

        preset_data = get_physics_preset(selected_name)
        if not preset_data:
            print(f"Preset '{selected_name}' not found.")
            return

        save_physics_settings(preset_data)
        print(f"Loaded physics preset: {selected_name}")

    def restore_defaults_and_save():
        physics_menu.reset_value()
        save_physics_settings(DEFAULT_PHYSICS_SETTINGS)

    settings = pm.Menu(
        title="Settings",
        width=WIDTH,
        height=HEIGHT,
        theme=pm.themes.THEME_GREEN,
    )
    settings._theme.widget_font_size = 25
    settings._theme.widget_font_color = BLACK
    settings._theme.widget_alignment = pm.locals.ALIGN_CENTER

    general_menu = pm.Menu(
        title="General Settings",
        width=WIDTH,
        height=HEIGHT,
        theme=pm.themes.THEME_GREEN,
    )
    general_menu._theme.widget_font_size = 25
    general_menu._theme.widget_font_color = BLACK
    general_menu._theme.widget_alignment = pm.locals.ALIGN_LEFT

    physics_menu = pm.Menu(
        title="Physics Settings",
        width=WIDTH,
        height=HEIGHT,
        theme=pm.themes.THEME_GREEN,
    )
    physics_menu._theme.widget_font_size = 25
    physics_menu._theme.widget_font_color = BLACK
    physics_menu._theme.widget_alignment = pm.locals.ALIGN_LEFT

    done = False

    def exit_settings():
        nonlocal done
        done = True

    def print_general_settings():
        print("\n\nGeneral settings:")
        data = general_menu.get_input_data()
        for key in data.keys():
            print(f"{key}\t:\t{data[key]}")

    # Main settings hub (no scrolling needed)
    settings.add.button("General Settings", general_menu)
    settings.add.button("Physics Settings", physics_menu)
    settings.add.button("Return To Main Menu", exit_settings)

    # General settings page
    general_menu.add.text_input(title="User Name : ", textinput_id="username")
    general_menu.add.dropselect(
        title="Graphics Level",
        items=graphics,
        dropselect_id="graphics level",
        default=0,
    )
    general_menu.add.dropselect_multiple(
        title="Window Resolution",
        items=resolution,
        dropselect_multiple_id="Resolution",
        open_middle=True,
        max_selected=1,
        selection_box_height=6,
    )
    general_menu.add.toggle_switch(title="Muisc", default=True, toggleswitch_id="music")
    general_menu.add.toggle_switch(title="Sounds", default=False, toggleswitch_id="sound")
    general_menu.add.selector(
        title="Difficulty\t",
        items=difficulty,
        selector_id="difficulty",
        default=0,
    )
    general_menu.add.range_slider(
        title="FOV",
        default=60,
        range_values=(50, 100),
        increment=1,
        value_format=lambda x: str(int(x)),
        rangeslider_id="fov",
    )
    general_menu.add.selector(
        title="Perspective",
        items=perspectives,
        default=0,
        style="fancy",
        selector_id="perspective",
    )
    general_menu.add.clock(
        clock_format="%d-%m-%y %H:%M:%S",
        title_format="Local Time : {0}",
    )
    general_menu.add.button(
        title="Print Settings",
        action=print_general_settings,
        font_color=WHITE,
        background_color=GREEN,
    )
    general_menu.add.button(title="Back", action=pm.events.BACK)

    # Physics settings page
    physics_menu.add.selector(
        title="Physics Profile",
        items=physics_profiles,
        selector_id="physics_profile",
        default=_profile_index(physics_data.get("physics_profile", "balanced")),
    )
    physics_menu.add.range_slider(
        title="Nose Offset",
        default=float(physics_data.get("sprite_angle_offset_deg", 0.0)),
        range_values=(-180.0, 180.0),
        increment=1.0,
        value_format=lambda x: f"{int(x):+d}",
        rangeslider_id="physics_offset",
    )
    physics_menu.add.range_slider(
        title="Speed Mult",
        default=float(physics_data.get("speed_multiplier", 1.0)),
        range_values=(0.3, 3.5),
        increment=0.05,
        value_format=lambda x: f"{x:.2f}",
        rangeslider_id="physics_speed",
    )
    physics_menu.add.range_slider(
        title="Turn Mult",
        default=float(physics_data.get("turn_multiplier", 1.0)),
        range_values=(0.3, 3.5),
        increment=0.05,
        value_format=lambda x: f"{x:.2f}",
        rangeslider_id="physics_turn",
    )
    physics_menu.add.text_input(
        title="Preset Name",
        default="my_preset",
        textinput_id="physics_preset_name",
    )
    preset_items = [(name, name) for name in load_physics_presets().keys()] or [("None", "")]
    preset_selector = physics_menu.add.selector(
        title="Load Preset",
        items=preset_items,
        selector_id="physics_preset_select",
        default=0,
    )
    physics_menu.add.button(
        title="Save Physics Settings",
        action=save_physics_from_menu,
        font_color=WHITE,
        background_color=CYAN,
    )
    physics_menu.add.button(
        title="Save Physics Preset",
        action=save_preset_from_menu,
        font_color=WHITE,
        background_color=BLUE,
    )
    physics_menu.add.button(
        title="Load Physics Preset",
        action=load_selected_preset_from_menu,
        font_color=WHITE,
        background_color=(70, 90, 180),
    )
    physics_menu.add.button(
        title="Restore Physics Defaults",
        action=restore_defaults_and_save,
        font_color=WHITE,
        background_color=RED,
    )
    physics_menu.add.button(title="Back", action=pm.events.BACK)

    while not done:
        settings.mainloop(screen, bgfun=draw_translucent_bg, disable_loop=True)
    return


def _fallback_settings_screen():
    """Fallback settings page when pygame_menu is not installed."""
    screen = pygame.display.get_surface()
    if screen is None:
        screen = pygame.display.set_mode((1600, 800))

    if not pygame.font.get_init():
        pygame.font.init()

    title_font = pygame.font.Font(None, 72)
    info_font = pygame.font.Font(None, 40)
    hint_font = pygame.font.Font(None, 32)

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                running = False

        screen.fill((22, 28, 40))

        title = title_font.render("SETTINGS", True, (240, 240, 240))
        info = info_font.render("pygame_menu is not installed.", True, (210, 210, 210))
        hint = hint_font.render("Press ESC, Enter, or click to return.", True, (170, 190, 220))

        screen.blit(title, title.get_rect(center=(screen.get_width() // 2, 220)))
        screen.blit(info, info.get_rect(center=(screen.get_width() // 2, 340)))
        screen.blit(hint, hint.get_rect(center=(screen.get_width() // 2, 410)))

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()