import pygame
from display_settings import load_display_settings
from Audio.pelimusat import GameSounds
from Audio import pelimusat
import json
import os


# LATAA TALLENNETUT ÄÄNENVOIMAKKUUSASETUKSET
def load_audio_settings():
    """LATAA ÄÄNENVOIMAKKUUS-ASETUKSET TIEDOSTOSTA"""
    # SETTINGS-TIEDOSTOT KANSIOSSA SIJAITSEVA TIEDOSTO
    audio_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "SETTINGS-tiedostot", "audio_settings.json")
    print(f"[GAMESTATEMANAGER] 📂 Etsitään: {audio_file}")
    
    if os.path.exists(audio_file):
        print(f"[GAMESTATEMANAGER] ✓ Tiedosto löytyi")
        try:
            with open(audio_file, 'r') as f:
                data = json.load(f)
                print(f"[GAMESTATEMANAGER] ✅ Ladattu: {data}")
                return data
        except (json.JSONDecodeError, IOError, OSError) as e:
            print(f"[GAMESTATEMANAGER] ❌ Virhe: {e}")
            pass
    else:
        print(f"[GAMESTATEMANAGER] ⚠️ Tiedosto ei ole olemassa: {audio_file}")
    
    print(f"[GAMESTATEMANAGER] 📋 Käytetään oletusarvoja")
    return {"music_volume": 0.8, "sfx_volume": 0.8}

def ensure_audio_settings_file():
    """VARMISTAA ETTÄ SETTINGS-TIEDOSTOT KANSIO JA audio_settings.json OVAT OLEMASSA"""
    audio_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "SETTINGS-tiedostot", "audio_settings.json")
    audio_dir = os.path.dirname(audio_file)
    
    # LUO KANSIO JOS SE EI OLE OLEMASSA
    if not os.path.exists(audio_dir):
        print(f"[GAMESTATEMANAGER] 📁 Luodaan kansio: {audio_dir}")
        try:
            os.makedirs(audio_dir, exist_ok=True)
            print(f"[GAMESTATEMANAGER] ✅ Kansio luotu")
        except OSError as e:
            print(f"[GAMESTATEMANAGER] ❌ Virhe kansion luomisessa: {e}")
            return
    
    # LUO TIEDOSTO OLETUSARVOILLA JOS SE EI OLE OLEMASSA
    if not os.path.exists(audio_file):
        print(f"[GAMESTATEMANAGER] 📝 Luodaan audio_settings.json oletusarvoilla...")
        try:
            default_settings = {"music_volume": 0.8, "sfx_volume": 0.8}
            with open(audio_file, 'w') as f:
                json.dump(default_settings, f)
            print(f"[GAMESTATEMANAGER] ✅ Tiedosto luotu: {audio_file}")
        except (IOError, OSError) as e:
            print(f"[GAMESTATEMANAGER] ❌ Virhe tiedoston luomisessa: {e}")


class GameStateManager:

    def __init__(self, initial_state):
        pygame.init()

        display = load_display_settings()
        flags = pygame.FULLSCREEN if display.get("fullscreen", False) else 0
        self.screen = pygame.display.set_mode((display["width"], display["height"]), flags)
        pygame.display.set_caption("Rocket Game")

        self.clock = pygame.time.Clock()
        self.running = True
        self.level_manager = None
        
        # VARMISTA ETTÄ AUDIOSÄÄDÖSKANSLÖ JA TIEDOSTOT OVA OLEMASSA
        ensure_audio_settings_file()
        
        # ALUSTA PELIN ÄÄNIJÄRJESTELMÄ
        self.sounds = GameSounds()
        self.sounds.set_master_volume(0.8)
        
        # LATAA TALLENNETUT ÄÄNENVOIMAKKUUSASETUKSET JA ASETA NE
        audio_settings = load_audio_settings()
        self.sounds.set_music_volume(audio_settings.get("music_volume", 0.8))
        self.sounds.set_sfx_volume(audio_settings.get("sfx_volume", 0.8))
        
        # ASETA GLOBAALI SOUNDS-VIITTAUS JOTTA MUUT PELIN OSAT VOIVAT KÄYTTÄÄ SITÄ
        pelimusat.game_sounds = self.sounds
        
        # ALOITA TAUSTAMUSIIKKI HETI PELIN ALKAESSA - LOOPPII KOKO PELIN AJAN
        self.sounds.play_music("pelimusa-root", loops=-1)

        self.state = initial_state
        self.state.manager = self

    def set_state(self, new_state):
        """VAIHTAA PELITILAN JA KUTSUU on_enter() -METODIA"""
        self.state = new_state
        self.state.manager = self
        # KUTSUU on_enter() UUDELLE TILALLE (ESIM. LATAA ASETUKSET KUN PÄÄVALIKKOON SIIRRYTÄÄN)
        if hasattr(self.state, 'on_enter'):
            self.state.on_enter()

    def run(self):
        """Pelin pääsilmukka"""

        while self.running:
            current_surface = pygame.display.get_surface()
            if current_surface is not None and current_surface != self.screen:
                self.screen = current_surface

            events = pygame.event.get()

            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False

            # Päivitä state
            if self.state:
                self.state.update(events)

            # Piirrä state
            if self.state:
                self.state.draw(self.screen)

            pygame.display.flip()

            self.clock.tick(60)

        # SULKEA ÄÄNIJÄRJESTELMÄ JA PYGAME ENNEN LOPETUSTA
        self.sounds.quit()
        pygame.quit()