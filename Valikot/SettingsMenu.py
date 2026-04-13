import pygame
from Valikot.menu_style import draw_dim_overlay, draw_menu_panel
from Audio import pelimusat
import json
import os

from physics_settings import (
    DEFAULT_PHYSICS_SETTINGS,
    get_physics_preset,
    load_physics_presets,
    load_physics_settings,
    save_physics_preset,
    save_physics_settings,
)
from display_settings import (
    load_display_settings,
    parse_resolution_label,
    resolution_items,
    resolution_to_label,
    save_display_settings,
)

#------------------------------------------------------
# AUDIO SETTINGS - ÄÄNENVOIMAKKUUKSIEN TALLENNUS
#------------------------------------------------------

# ÄÄNIASETUKSIEN TIEDOSTON SIJAINTI - SETTINGS-TIEDOSTOT KANSIOSSA
AUDIO_SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "SETTINGS-tiedostot", "audio_settings.json")

def load_audio_settings():
    """LATAA ÄÄNENVOIMAKKUUS-ASETUKSET TIEDOSTOSTA"""
    print(f"[LOAD_AUDIO] 📂 Etsitään:{AUDIO_SETTINGS_FILE}")
    if os.path.exists(AUDIO_SETTINGS_FILE):
        print(f"[LOAD_AUDIO] ✓ Tiedosto löytyi")
        try:
            with open(AUDIO_SETTINGS_FILE, 'r') as f:
                data = json.load(f)
                print(f"[LOAD_AUDIO] ✅ Ladattu: {data}")
                return data
        except (json.JSONDecodeError, IOError, OSError) as e:
            print(f"[LOAD_AUDIO] ❌ Virhe: {e}")
            pass
    else:
        print(f"[LOAD_AUDIO] ⚠️ Tiedosto ei ole olemassa: {AUDIO_SETTINGS_FILE}")
    return {"music_volume": 0.8, "sfx_volume": 0.8}

def save_audio_settings(music_volume, sfx_volume):
    """TALLENTAA ÄÄNENVOIMAKKUUS-ASETUKSET TIEDOSTOON"""
    print(f"[SAVE_AUDIO] 💾 Tallennetaan: {AUDIO_SETTINGS_FILE}")
    print(f"[SAVE_AUDIO] 💾 Arvot: Musiikki={int(music_volume*100)}%, SFX={int(sfx_volume*100)}%")
    try:
        # VARMISTA ETTÄ KANSIO ON OLEMASSA
        directory = os.path.dirname(AUDIO_SETTINGS_FILE)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        with open(AUDIO_SETTINGS_FILE, 'w') as f:
            json.dump({"music_volume": music_volume, "sfx_volume": sfx_volume}, f)
        print(f"[SAVE_AUDIO] ✅ TALLENNETTU ONNISTUNEESTI: {AUDIO_SETTINGS_FILE}")
    except (IOError, OSError) as e:
        print(f"[SAVE_AUDIO] ❌ VIRHE ÄÄNIASETUKSIEN TALLENTAMISESSA: {e}")
        print(f"[SAVE_AUDIO] ❌ POLKU: {AUDIO_SETTINGS_FILE}")

#------------------------------------------------------
#Asennus: pip install pygame-menu
#------------------------------------------------------



# Valikoiden koko suhteessa ikkunan kokoon (esim. 70%)
def get_menu_size():
    screen = pygame.display.get_surface()
    if screen is not None:
        width = int(screen.get_width() * 0.7)
        height = int(screen.get_height() * 0.7)
        # Varmista minimikoko
        width = max(width, 400)
        height = max(height, 300)
        return width, height
    return 700, 500

# Standard RGB colors
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
CYAN = (0, 100, 100)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

THEME_BG = (20, 44, 68, 205)
THEME_TITLE_BG = (34, 82, 126, 230)
THEME_TEXT = (240, 247, 255)
THEME_SELECTION = (188, 221, 255)


def main():



    def print_general_settings():
        print("\n\nGeneral settings:")
        data = general_menu.get_input_data()
        for key in data.keys():
            print(f"{key}\t:\t{data[key]}")

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
                except (AttributeError, TypeError):
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

    def exit_settings():
        nonlocal done, selected_action
        selected_action = "return"
        done = True

    def start_hazard_test_level():
        nonlocal done, selected_action
        selected_action = "start_test_level"
        done = True

    def start_hazard_test2_level():
        nonlocal done, selected_action
        selected_action = "start_test2_level"
        done = True

    def apply_display_settings_from_menu():
        nonlocal screen, frozen_bg
        print(f"[APPLY_SETTINGS] 🎮 Apply Settings painike painettu!")
        data = general_menu.get_input_data()
        print(f"[APPLY_SETTINGS] 📊 Menu data: {data}")

        selected_resolution = data.get("resolution", (("1280x720", "1280x720"), 0))[0][1]
        selected_mode = data.get("display_mode", (("Windowed", "windowed"), 0))[0][1]
        
        # HAKU ÄÄNENVOIMAKKUUDEN ARVOISTA
        music_volume = float(data.get("music_volume", 0.8))
        sfx_volume = float(data.get("sfx_volume", 0.8))
        print(f"[APPLY_SETTINGS] 🎵 Haetut äänenvoimakkuudet: Musiikki={int(music_volume*100)}%, SFX={int(sfx_volume*100)}%")

        # Käytetään labelia suoraan ja parsitaan siitä width ja height
        width, height = parse_resolution_label(selected_resolution)
        fullscreen = str(selected_mode).strip().lower() == "fullscreen"

        # Tallennetaan täsmälleen valittu resoluutio
        save_display_settings({
            "width": width,
            "height": height,
            "fullscreen": fullscreen
        })
        
        # TALLENNETAAN ÄÄNENVOIMAKKUUS ASETUKSET JA ASETETAAN PELIIN
        save_audio_settings(music_volume, sfx_volume)
        if pelimusat.game_sounds:
            pelimusat.game_sounds.set_music_volume(music_volume)
            pelimusat.game_sounds.set_sfx_volume(sfx_volume)
            print(f"[APPLY_SETTINGS] ✅ ÄÄNENVOIMAKKUUS ASETETTU PELIIN - Musiikki: {int(music_volume*100)}%, Tehosteet: {int(sfx_volume*100)}%")

        # Käytä windowed-tilassa oletusflagia (näkyy yläpalkki), fullscreenissä FULLSCREEN
        flags = pygame.FULLSCREEN if fullscreen else 0
        screen = pygame.display.set_mode((width, height), flags)
        frozen_bg = screen.copy()
        # Luo valikot uudelleen uusilla mitoilla
        create_menus()

    physics_data = load_physics_settings()
    display_data = load_display_settings()
    display_modes = [
        ("Windowed", "windowed"),
        ("Fullscreen", "fullscreen"),
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

    def _index_for_value(items, value):
        target = str(value).strip().lower()
        for i, (_, item_value) in enumerate(items):
            if str(item_value).strip().lower() == target:
                return i
        return 0

    try:
        import pygame_menu as pm
    except ImportError:
        pm = None

    if pm is None:
        _fallback_settings_screen()
        return

    screen = pygame.display.get_surface()
    if screen is None:
        screen = pygame.display.set_mode((1600, 800))

    # Pause-style translucent backdrop: frozen frame + dark alpha overlay.
    frozen_bg = screen.copy()

    menu_theme = pm.themes.THEME_DARK.copy()
    menu_theme.background_color = THEME_BG
    menu_theme.title_background_color = THEME_TITLE_BG
    menu_theme.title_font_color = THEME_TEXT
    menu_theme.widget_font_color = THEME_TEXT
    menu_theme.selection_color = THEME_SELECTION
    menu_theme.widget_font_size = 25
    menu_theme.widget_alignment = pm.locals.ALIGN_CENTER
    menu_theme.title_font_size = 46
    menu_theme.widget_padding = 10

    def create_menus():
        nonlocal settings, general_menu, physics_menu, WIDTH, HEIGHT, display_data, audio_data
        WIDTH, HEIGHT = get_menu_size()
        display_data = load_display_settings()  # Lataa aina tuore display_data tiedostosta
        audio_data = load_audio_settings()  # LATAA AINA TUORE AUDIO_DATA TIEDOSTOSTA
        settings = pm.Menu(
            title="Settings",
            width=WIDTH,
            height=HEIGHT,
            theme=menu_theme,
        )
        general_menu = pm.Menu(
            title="General Settings",
            width=WIDTH,
            height=HEIGHT,
            theme=menu_theme,
        )
        general_menu._theme.widget_alignment = pm.locals.ALIGN_LEFT
        physics_menu = pm.Menu(
            title="Physics Settings",
            width=WIDTH,
            height=HEIGHT,
            theme=menu_theme,
        )
        physics_menu._theme.widget_alignment = pm.locals.ALIGN_LEFT

        # General settings page
        resolution = resolution_items()
        general_menu.add.selector(
            title="Window Resolution",
            items=resolution,
            selector_id="resolution",
            default=_index_for_value(
                resolution,
                resolution_to_label(display_data.get("width", 1280), display_data.get("height", 720)),
            ),
        )
        general_menu.add.selector(
            title="Display Mode",
            items=display_modes,
            selector_id="display_mode",
            default=_index_for_value(
                display_modes,
                "fullscreen" if display_data.get("fullscreen", False) else "windowed",
            ),
        )
        
        # CALLBACK-FUNKTIOT ÄÄNENVOIMAKKUUKSIEN REAALIAIKAISELLE PÄIVITTÄMISELLE JA TALLENNUKSELLE
        def on_music_volume_change(value):
            """SOITETAAN KUN MUSIIKIN ÄÄNENVOIMAKKUUS MUUTTUU - TALLENTAA ASETUKSET HETI"""
            print(f"[SETTINGS_CALLBACK] 🎵 Musiikin äänenvoimakkuus muuttui: {value} ({int(value*100)}%)")
            if pelimusat.game_sounds:
                pelimusat.game_sounds.set_music_volume(value)
                print(f"[SETTINGS_CALLBACK] ✓ Asetettu peliin")
            # HAKU NYKYINEN SFX-VOLUME JA TALLENNA MOLEMMAT HETI
            data = general_menu.get_input_data()
            print(f"[SETTINGS_CALLBACK] 📊 Menu data: {data}")
            try:
                sfx_vol = float(data.get("sfx_volume", 0.8))
                save_audio_settings(value, sfx_vol)
                print(f"[SETTINGS_CALLBACK] ✅ TALLENNETTU: Musiikki={int(value*100)}%, SFX={int(sfx_vol*100)}%")
            except (ValueError, TypeError) as e:
                # EI TALLENNETA JOS KONVERSIO EPÄONNISTUU, MUTTA ÄÄNENVOIMAKKUUS ASETETAAN PELIIN
                print(f"[SETTINGS_CALLBACK] ❌ VIRHE tallentamisessa: {e}")

        def on_sfx_volume_change(value):
            """SOITETAAN KUN TEHOSTEIDEN ÄÄNENVOIMAKKUUS MUUTTUU - TALLENTAA ASETUKSET HETI"""
            print(f"[SETTINGS_CALLBACK] 🔊 SFX äänenvoimakkuus muuttui: {value} ({int(value*100)}%)")
            if pelimusat.game_sounds:
                pelimusat.game_sounds.set_sfx_volume(value)
                print(f"[SETTINGS_CALLBACK] ✓ Asetettu peliin")
            # HAKU NYKYINEN MUSIC-VOLUME JA TALLENNA MOLEMMAT HETI
            data = general_menu.get_input_data()
            print(f"[SETTINGS_CALLBACK] 📊 Menu data: {data}")
            try:
                music_vol = float(data.get("music_volume", 0.8))
                save_audio_settings(music_vol, value)
                print(f"[SETTINGS_CALLBACK] ✅ TALLENNETTU: Musiikki={int(music_vol*100)}%, SFX={int(value*100)}%")
            except (ValueError, TypeError) as e:
                # EI TALLENNETA JOS KONVERSIO EPÄONNISTUU, MUTTA ÄÄNENVOIMAKKUUS ASETETAAN PELIIN
                print(f"[SETTINGS_CALLBACK] ❌ VIRHE tallentamisessa: {e}")
        
        # ÄÄNENVOIMAKKUUDEN SÄÄTÖSLIDERIT - ONLINE CALLBACK PÄIVITYKSELLÄ
        general_menu.add.range_slider(
            title="Music Volume",
            default=audio_data.get("music_volume", 0.8),
            range_values=(0.0, 1.0),
            increment=0.05,
            value_format=lambda x: f"{int(x * 100)}%",
            rangeslider_id="music_volume",
            onchange=on_music_volume_change,
        )
        general_menu.add.range_slider(
            title="Sound Effects Volume",
            default=audio_data.get("sfx_volume", 0.8),
            range_values=(0.0, 1.0),
            increment=0.05,
            value_format=lambda x: f"{int(x * 100)}%",
            rangeslider_id="sfx_volume",
            onchange=on_sfx_volume_change,
        )
        general_menu.add.button(
            title="Apply Settings",
            action=apply_display_settings_from_menu,
            font_color=WHITE,
            background_color=(54, 120, 82),
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
        nonlocal preset_selector
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

        # Main settings hub (no scrolling needed)
        settings.add.button("General Settings", general_menu)
        settings.add.button("Physics Settings", physics_menu)
        settings.add.button("Start Hazard Test Level", start_hazard_test_level)
        settings.add.button("Start Hazard Test2 Level", start_hazard_test2_level)
        settings.add.button("Return To Main Menu", exit_settings)

    # Alustava luonti
    settings = general_menu = physics_menu = preset_selector = None
    WIDTH = HEIGHT = 0
    audio_data = load_audio_settings()  # LATAA AUDIO-ASETUKSET ALUSTA LÄHTIEN
    create_menus()

    def draw_translucent_bg():
        screen.blit(frozen_bg, (0, 0))
        draw_dim_overlay(screen)

    menu_theme = pm.themes.THEME_DARK.copy()
    menu_theme.background_color = THEME_BG
    menu_theme.title_background_color = THEME_TITLE_BG
    menu_theme.title_font_color = THEME_TEXT
    menu_theme.widget_font_color = THEME_TEXT
    menu_theme.selection_color = THEME_SELECTION
    menu_theme.widget_font_size = 25
    menu_theme.widget_alignment = pm.locals.ALIGN_CENTER
    menu_theme.title_font_size = 46
    menu_theme.widget_padding = 10

    physics_data = load_physics_settings()
    preset_selector = None

    display_data = load_display_settings()

    resolution = resolution_items()

    display_modes = [
        ("Windowed", "windowed"),
        ("Fullscreen", "fullscreen"),
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



    settings = pm.Menu(
        title="Settings",
        width=WIDTH,
        height=HEIGHT,
        theme=menu_theme,
    )

    general_menu = pm.Menu(
        title="General Settings",
        width=WIDTH,
        height=HEIGHT,
        theme=menu_theme,
    )
    general_menu._theme.widget_alignment = pm.locals.ALIGN_LEFT

    physics_menu = pm.Menu(
        title="Physics Settings",
        width=WIDTH,
        height=HEIGHT,
        theme=menu_theme,
    )
    physics_menu._theme.widget_alignment = pm.locals.ALIGN_LEFT

    done = False
    selected_action = "return"

    def exit_settings():
        nonlocal done, selected_action
        selected_action = "return"
        done = True

    def start_hazard_test_level():
        nonlocal done, selected_action
        selected_action = "start_test_level"
        done = True

    def start_hazard_test2_level():
        nonlocal done, selected_action
        selected_action = "start_test2_level"
        done = True



    def _index_for_value(items, value):
        target = str(value).strip().lower()
        for i, (_, item_value) in enumerate(items):
            if str(item_value).strip().lower() == target:
                return i
        return 0

    def apply_display_settings_from_menu():
        nonlocal screen, frozen_bg
        data = general_menu.get_input_data()
        selected_resolution = data.get("resolution", (("1280x720", "1280x720"), 0))[0][1]
        selected_mode = data.get("display_mode", (("Windowed", "windowed"), 0))[0][1]
        
        # HAKU ÄÄNENVOIMAKKUUDEN ARVOISTA
        music_volume = float(data.get("music_volume", 0.8))
        sfx_volume = float(data.get("sfx_volume", 0.8))

        width, height = parse_resolution_label(selected_resolution)
        fullscreen = str(selected_mode).strip().lower() == "fullscreen"

        new_display = {
            "width": width,
            "height": height,
            "fullscreen": fullscreen,
        }
        save_display_settings(new_display)
        
        # TALLENNETAAN ÄÄNENVOIMAKKUUS ASETUKSET JA ASETETAAN PELIIN
        save_audio_settings(music_volume, sfx_volume)
        if pelimusat.game_sounds:
            pelimusat.game_sounds.set_music_volume(music_volume)
            pelimusat.game_sounds.set_sfx_volume(sfx_volume)
            print(f"ÄÄNENVOIMAKKUUS ASETETTU - Musiikki: {int(music_volume*100)}%, Tehosteet: {int(sfx_volume*100)}%")

        # Käytä windowed-tilassa oletusflagia (näkyy yläpalkki), fullscreenissä FULLSCREEN
        flags = pygame.FULLSCREEN if fullscreen else 0
        screen = pygame.display.set_mode((width, height), flags)
        frozen_bg = screen.copy()
        # Luo valikot uudelleen uusilla mitoilla
        create_menus()

    # Main settings hub (no scrolling needed)
    settings.add.button("General Settings", general_menu)
    settings.add.button("Physics Settings", physics_menu)
    settings.add.button("Start Hazard Test Level", start_hazard_test_level)
    settings.add.button("Start Hazard Test2 Level", start_hazard_test2_level)
    settings.add.button("Return To Main Menu", exit_settings)

    # General settings page
    general_menu.add.selector(
        title="Window Resolution",
        items=resolution,
        selector_id="resolution",
        default=_index_for_value(
            resolution,
            resolution_to_label(display_data.get("width", 1280), display_data.get("height", 720)),
        ),
    )
    general_menu.add.selector(
        title="Display Mode",
        items=display_modes,
        selector_id="display_mode",
        default=_index_for_value(
            display_modes,
            "fullscreen" if display_data.get("fullscreen", False) else "windowed",
        ),
    )
    # ÄÄNENVOIMAKKUUDEN SÄÄTÖSLIDERIT
    general_menu.add.range_slider(
        title="Music Volume",
        default=0.8,
        range_values=(0.0, 1.0),
        increment=0.05,
        value_format=lambda x: f"{int(x * 100)}%",
        rangeslider_id="music_volume",
    )
    general_menu.add.range_slider(
        title="Sound Effects Volume",
        default=0.8,
        range_values=(0.0, 1.0),
        increment=0.05,
        value_format=lambda x: f"{int(x * 100)}%",
        rangeslider_id="sfx_volume",
    )
    general_menu.add.button(
        title="Apply Settings",
        action=apply_display_settings_from_menu,
        font_color=WHITE,
        background_color=(54, 120, 82),
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
    apply_display_settings_from_menu()
    return selected_action


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
    panel_width = min(900, screen.get_width() - 120)
    panel_height = min(460, screen.get_height() - 120)
    panel_rect = pygame.Rect(
        screen.get_width() // 2 - panel_width // 2,
        screen.get_height() // 2 - panel_height // 2,
        panel_width,
        panel_height,
    )

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
        draw_dim_overlay(screen)
        draw_menu_panel(screen, panel_rect, "SETTINGS", "Configuration")

        title = title_font.render("SETTINGS", True, (240, 240, 240))
        info = info_font.render("pygame_menu is not installed.", True, (210, 210, 210))
        hint = hint_font.render("Press ESC, Enter, or click to return.", True, (170, 190, 220))

        screen.blit(title, title.get_rect(center=(screen.get_width() // 2, panel_rect.top + 70)))
        screen.blit(info, info.get_rect(center=(screen.get_width() // 2, panel_rect.top + 190)))
        screen.blit(hint, hint.get_rect(center=(screen.get_width() // 2, panel_rect.top + 260)))

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()