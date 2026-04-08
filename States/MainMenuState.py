import pygame
import json
import os

from States.GameState import GameState
from Valikot.MainMenu import MainMenu


class MainMenuState(GameState):

    def __init__(self, manager=None):
        super().__init__(manager)
        # VÄLITÄ SOUNDS-OBJEKTI MENULLE HOVER-EFEKTEJÄ VARTEN
        self.menu = MainMenu(sounds=manager.sounds if manager else None)
    
    def on_enter(self):
        """KUTSUTAAN KUN PÄÄVALIKKOON SIIRRYTÄÄN - LATAA TALLENNETUT ASETUKSET"""
        print("[MAINMENU] on_enter() KUTSUTTU - LADATAAN ÄÄNIASETUKSET")
        self._load_audio_settings()
    
    def _load_audio_settings(self):
        """LATAA JA ASETTAA TALLENNETUN ÄÄNENVOIMAKKUUDEN PELIIN"""
        print("[MAINMENU] _load_audio_settings() ALOITETTU")
        # SETTINGS-TIEDOSTOT KANSIOSSA SIJAITSEVA TIEDOSTO
        audio_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "SETTINGS-tiedostot", "audio_settings.json")
        print(f"[MAINMENU] 🔍 Etsitään: {audio_file}")
        
        if not os.path.exists(audio_file):
            # ASETUKSILLA EI OLE TIEDOSTOA, KÄYTÄ OLETUKSINTA
            print(f"[MAINMENU] ⚠️ TIEDOSTO EI LÖYTYNYT - KÄYTETÄÄN OLETUSARVOJA")
            return
        
        print(f"[MAINMENU] 📂 Luetaan {audio_file}")
        try:
            with open(audio_file, 'r') as f:
                audio_data = json.load(f)
                print(f"[MAINMENU] ✓ JSON LADATTU: {audio_data}")
        except (IOError, OSError) as e:
            print(f"[MAINMENU] ❌ VIRHE TIEDOSTON AVAAMISESSA: {e}")
            return
        except json.JSONDecodeError as e:
            print(f"[MAINMENU] ❌ VIRHE JSON-JÄSENNYKSESSÄ: {e}")
            return
        
        try:
            if self.manager and self.manager.sounds:
                music_vol = float(audio_data.get("music_volume", 0.8))
                sfx_vol = float(audio_data.get("sfx_volume", 0.8))
                self.manager.sounds.set_music_volume(music_vol)
                self.manager.sounds.set_sfx_volume(sfx_vol)
                print(f"[MAINMENU] ✅ ÄÄNENVOIMAKKUUS ASETETTU - MUSIIKKI: {int(music_vol*100)}%, TEHOSTEET: {int(sfx_vol*100)}%")
            else:
                print(f"[MAINMENU] ❌ manager tai sounds on None!")
        except (ValueError, TypeError) as e:
            print(f"[MAINMENU] ❌ VIRHE ARVOJEN KONVERTOINNISSA: {e}")

    def update(self, events):

        action = self.menu.handle_events(events)

        if action == "start":
            # SOITA PELIN ALKAA -ÄÄNI
            self.manager.sounds.play_sfx("game_start")
            try:
                from States.PlayState import PlayState
                self.manager.set_state(PlayState(self.manager))
            except Exception as exc:
                # Keep the menu active if gameplay state is not yet wired.
                print(f"Could not start PlayState: {exc}")

        elif action == "settings":
            # SOITA NAPPIA PAINETTAESSA -ÄÄNI
            self.manager.sounds.play_sfx("button_hover")
            print("[MAINMENU] ⚙️ Settings-nappia painettu")
            try:
                from Valikot.SettingsMenu import main as settings_menu_main
                from States.PlayState import PlayState
                from Tasot.LevelManager import LevelManager

                print("[MAINMENU] 📂 Avataan Settings-valikko...")
                settings_action = settings_menu_main()
                print("[MAINMENU] 📂 Settings-valikko sulkeutui - Ladataan asetukset uudelleen")
                
                # LATAA ÄÄNIASETUKSET UUDELLEEN KUN SETTINGS-VALIKKO SULKEUTUU
                # (on_enter ei kutsutaan kun palataan, joten tarvitsemme tämän)
                self._load_audio_settings()
                
                current_surface = pygame.display.get_surface()
                if current_surface is not None:
                    self.manager.screen = current_surface
                if settings_action == "start_test_level":
                    test_level_manager = LevelManager(self.manager.screen, level_numbers=[0])
                    self.manager.set_state(PlayState(self.manager, level_manager=test_level_manager))
                elif settings_action == "start_test2_level":
                    test_level_manager = LevelManager(self.manager.screen, level_numbers=[6])
                    self.manager.set_state(PlayState(self.manager, level_manager=test_level_manager))
            except Exception as exc:
                print(f"Could not open settings menu: {exc}")

        elif action == "quit":
            self.manager.running = False

    def draw(self, screen):
        self.menu.draw(screen)