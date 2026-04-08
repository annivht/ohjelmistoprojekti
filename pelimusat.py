"""
================================================================================
PELIMUSAT.PY - PELIN ÄÄNIEN JA MUSIIKIN HALLINTAJÄRJESTELMÄ

TÄMÄ LUOKKA VASTAA KAIKKIEN PELIN ÄÄNIEN JA MUSIIKIN TOISTAMISESTA JA HALLINNASTA.
LUOKKA TUKEE SEKÄ TAUSTAMUSIIKKIA ETTÄ ÄÄNITEHOSTEIDEN (SFX) TOISTAMISTA
ERIKSEEN HALLITTAVILLA ÄÄNENVOIMAKKUUDEN ASETUKSILLA.

OMINAISUUDET:
- ÄÄNIEN JA MUSIIKIN KATEGORIOITU HALLINTA
- HELPPO LISÄTÄ UUSIA ÄÄNIÄ ILMAN KOODIN MUUTTAMISTA
- ÄÄNENVOIMAKKUUDEN SÄÄTÖMAHDOLLISUUS (PÄÄÄÄNI, TEHOSTEET, MUSIIKKI)
- ÄÄNIEN DYNAAMINEN LISÄÄMINEN AJON AIKANA
- KAIKKI ÄÄNIEN POLUT MÄÄRITELTY YLÄOSASSA HELPPOON MUOKKAUKSEEN

KÄYTTÖESIMERKKI:
    sounds = GameSounds()
    sounds.set_master_volume(0.8)
    sounds.play_sfx("laser_fire")
    sounds.play_music("pelimusa-root")

================================================================================
"""

import pygame
import os
from pathlib import Path


class GameSounds:
    """
    PELIN ÄÄNITEHOSTEET JA MUSIIKIN HALLINNOINTIJÄRJESTELMÄ
    
    HALLINNOI KAIKKIA PELIN ÄÄNIÄ JA MUSIIKKIA YHDELLÄ LUOKALLA.
    TUKEE KATEGORIOITUJA ÄÄNITEHOSTEIDEN HALLINTAA JA ERILLISTÄ MUSIIKIN SÄÄTÖÄ.
    """

    # ============================================================================
    # ÄÄNIKONFIGURAATION MÄÄRITYS - HELPPO MUOKATA ÄÄNIEN POLUT TÄSSÄ
    # ============================================================================

    # KANSIOPOLKU JOHON KAIKKI ÄÄNET SIJAITSEVAT
    SOUNDS_DIR = "Aanet"

    # TAUSTAMUSIIKKI - MÄÄRITÄ TÄSSÄ MUSIIKIN NIMI JA POLKU
    BACKGROUND_MUSIC = {
        # KÄYTTÖ: GameStateManager.__init__() - play_music("pelimusa-root", loops=-1)
        # KUVAUS: PELIN TAUSTAMUSIIKKI JOKA SOII KOKO PELIN AJAN LOOPISSA
        "pelimusa-root": "Aanet/pelimusa-root.mp3",
    }

    # SOUND EFFECTS - KATEGORISOIDUT ÄÄNITEHOSTEET
    # HELPPO LISÄTÄ UUSIA KATEGORIOITA TAI ÄÄNIÄ
    SOUND_EFFECTS = {
        "WEAPONS": {
            # KÄYTTÖ: PlayerWeapons.shoot() METODI - L-NAPPI
            #         Sijainti: PLAYER_LUOKAT/PlayerWeapons.py rivi ~81
            # KUVAUS: SOITETAAN KUN PELAAJA AMPUU LASEREJA (L-NAPPI)
            "laser_fire": "Aanet/LASER-L.mp3",
            
            # KÄYTTÖ: PlayerWeapons.shoot_with() METODI - P-NAPPI
            #         Sijainti: PLAYER_LUOKAT/PlayerWeapons.py rivi ~182
            # KUVAUS: SOITETAAN KUN PELAAJA AMPUU AMMUSTA (P-NAPPI)
            "ammus_fire": "Aanet/ammus-P-nappi.mp3",
        },
        "ENEMY_ACTIONS": {
            # KÄYTTÖ: Enemy.py - update() METODI, ENEMY SHOOTING LOGIIKAN YHTEYDESSÄ
            #         Sijainti: Enemy.py rivi ~100
            # KUVAUS: SOITETAAN KUN VASTUSTAJA AMPUU AMMUSTA
            "enemy_shoot": "Aanet/ENEMY-LASER.mp3",
            "enemy_explosion": "Aanet/KIVI-HAJOAA.mp3",

        },
        "BOSS_ACTIONS": {
            # KÄYTTÖ: Boss.py - update() METODI, BOSS SHOOTING LOGIIKAN YHTEYDESSÄ
            #         Sijainti: Boss.py rivi ~100
            # KUVAUS: SOITETAAN KUN BOSS AMPUU AMMUSTA
            #"boss_shoot": "Aanet/boss-ampuu-ammus.mp3",
            "boss_explosion": "Aanet/BIGBOSS-EXPLOSION.mp3",
            "boss_sound": "Aanet/BIGBOSS-SOUND.mp3",
            #"boss_rocket_launch": "Aanet/boss-laukaisee-rocketin.mp3",
        },
        "BOMBS": {
            # KÄYTTÖ: Bomb.py - update() METODI, BOMB EXPLOSION LOGIIKAN YHTEYDESSÄ
            #         Sijainti: Bomb.py rivi ~100
            # KUVAUS: SOITETAAN KUN POMMI HAJOAA
            "bomb_explosion": "Aanet/BOSS-BOMB.mp3",
        },

        "COLLISIONS": {
            # KÄYTTÖ: RocketGame.py - update() METODI, HAZARD_EFFECTS KÄSITTELYN YHTEYDESSÄ
            #         Sijainti: RocketGame.py rivi ~1090
            # KUVAUS: SOITETAAN KUN METEORITTI OSUU PELAAJAAN JA PELAAJA OTTAA VAHINKOA
            "meteor_hits_player": "Aanet/KIVI-HAJOAA.mp3",
            
            # KÄYTTÖ: VALMIINA INTEGRAATION ODOTUKSESSA (EI VIELÄ KÄYTÖSSÄ)
            # KUVAUS: PITÄISI SOIDA KUN PELAAJ OSUU METEORIIN AMMUKSELLA
            "player_hits_meteor": "Aanet/player-osuu-meteoriitti-hajoaa-osiin.mp3",
        },
        "MENU": {
            # KÄYTTÖ: MainMenu.draw() METODI - hover-tarkistus
            #         Sijainti: Valikot/MainMenu.py rivi ~161
            # KUVAUS: SOITETAAN KUN HIIRI SIIRTYY MENU-NAPIN PÄÄLLE (HOVER EFEKTI)
            "button_hover": "Aanet/menu-nappi-onHover.mp3",
            
            # KÄYTTÖ: MainMenuState.update() METODI - action == "start" KOHDALLA
            #         Sijainti: States/MainMenuState.py rivi ~20
            # KUVAUS: SOITETAAN KUN PELAAJA KLIKKAA "START GAME" NAPPIA MENUSSA
            "game_start": "Aanet/peli-alkaa-menu-button-onClick.mp3",
        },
    }

    # ============================================================================
    # KATEGORIAN ÄÄNIVOIMAKKUUDEN MAPPING
    # ============================================================================
    # MÄÄRITTÄÄ MIHIN KATEGORIAAN KUKIN ÄÄNITEHOSTE KUULUU
    SOUND_CATEGORY_MAP = {
        # WEAPONS
        "laser_fire": "WEAPONS",
        "ammus_fire": "WEAPONS",
        # COLLISIONS
        "meteor_hits_player": "COLLISIONS",
        "player_hits_meteor": "COLLISIONS",
        # MENU
        "button_hover": "MENU",
        "game_start": "MENU",
        # ENEMY_ACTIONS
        "enemy_shoot": "ENEMY_ACTIONS",
        "enemy_explosion": "ENEMY_ACTIONS",
        # BOSS_ACTIONS
        "boss_explosion": "BOSS_ACTIONS",
        "boss_sound": "BOSS_ACTIONS",
        # BOMBS
        "bomb_explosion": "BOMBS",
    }

    # ============================================================================
    # INDIVIDUAALINEN ÄÄNENVOIMAKKUUS KARTAUS
    # ============================================================================
    # ASETA TÄSSÄ JOKAISEN ÄÄNEN OMAT ÄÄNENVOIMAKKUUSARVOT (0.0 - 1.0)
    # ESIMERKKI: "laser_fire": 0.5 = laser puoleen voimakkuuteen
    INDIVIDUAL_SOUND_VOLUMES = {
        "laser_fire": 0.6,           # LASER LUJALLA - SÄÄDÄ TÄÄLLÄ! (0.6 = 60%)
        "ammus_fire": 1.0,           # P-NAPPI AMMO
        "enemy_shoot": 0.8,          # ENEMY AMPUU
        "enemy_explosion": 1.0,      # ENEMY HAJOAA
        "boss_explosion": 1.0,       # BOSS HAJOAA
        "boss_sound": 0.9,           # BOSS ÄÄNI
        "meteor_hits_player": 0.8,   # METEORITTI OSUU
        "player_hits_meteor": 0.8,   # PLAYER OSUU METEORIIN
        "button_hover": 0.7,         # MENU HOVER
        "game_start": 1.0,           # PELI ALKAA
        "bomb_explosion": 1.0,       # POMMI RÄJÄHTÄÄ
    }

    # ============================================================================
    # ALUSTUS JA PYGAME MIXER KONFIGURAATIO
    # ============================================================================

    def __init__(self, mixer_frequency=44100, mixer_size=-16, mixer_channels=8):
        """
        ALUSTAA PYGAME MIXER JA LATAA KAIKKI ÄÄNITIEDOSTOT MUISTIIN
        
        PARAMETRIT:
            mixer_frequency (int): ÄÄNEN NÄYTTEENOTTOTAAJUUS HZ:SSÄ (OLETUS: 44100)
            mixer_size (int): ÄÄNEN NÄYTTEEN KOKO BITEISSÄ, NEGATIIVINEN = SIGNED (OLETUS: -16)
            mixer_channels (int): KUINKA MONTA ÄÄNITEHOSTETTA VOI SOIDA SAMANAIKAISESTI (OLETUS: 8)
        """
        # ALUSTA PYGAME MIXER PARAMETREIN
        pygame.mixer.init(frequency=mixer_frequency, size=mixer_size, channels=mixer_channels)

        # AKTIIVISEN MUSIIKIN SEURANTA
        self.current_music = None

        # STORED SOUND OBJECTS - ÄÄNIEN VÄLIMUISTIIN LATAAMINEN
        self.music_dict = {}
        self.sfx_dict = {}

        # ÄÄNENVOIMAKKUUDEN ASETUKSET
        self.master_volume = 1.0
        self.music_volume = 1.0
        self.sfx_volume = 1.0
        
        # KATEGORIAKOHTAINEN ÄÄNENVOIMAKKUUS (0.0 - 1.0)
        self.weapons_volume = 1.0
        self.collisions_volume = 1.0
        self.menu_volume = 1.0
        self.enemy_actions_volume = 1.0
        self.boss_actions_volume = 1.0
        self.bombs_volume = 1.0

        # LATAA KAIKKI ÄÄNET MUISTIIN
        self.load_sounds()

    # ============================================================================
    # ÄÄNITIEDOSTOJEN LATAAMINEN
    # ============================================================================

    def load_sounds(self):
        """
        LATAA KAIKKI ÄÄNITIEDOSTOT MUSIC JA SFX DIKTIONAAREISTA MUISTIIN.
        KUTSUTAAN AUTOMAATTISESTI __init__() METODISSA.
        VIRHEENKÄSITTELY: ILMOITTAA JOS ÄÄNITIEDOSTOA EI LÖYDY.
        """
        # LATAA TAUSTAMUSIIKKI
        for music_name, music_path in self.BACKGROUND_MUSIC.items():
            if not os.path.exists(music_path):
                print(f"⚠️  VAROITUS: MUSIIKKITIEDOSTO EI LÖYTYNYT - {music_path}")
                continue
            try:
                self.music_dict[music_name] = music_path
                print(f"✓ MUSIIKKI LADATTU: {music_name}")
            except pygame.error as e:
                print(f"❌ VIRHE MUSIIKIN LATAAMISESSA {music_path}: {e}")

        # LATAA ÄÄNITEHOSTEET KAIKISTA KATEGORIOISTA
        for category, sounds in self.SOUND_EFFECTS.items():
            for sound_name, sound_path in sounds.items():
                if not os.path.exists(sound_path):
                    print(f"⚠️  VAROITUS: ÄÄNITEHOSTE EI LÖYTYNYT - {sound_path}")
                    continue
                try:
                    sound_obj = pygame.mixer.Sound(sound_path)
                    self.sfx_dict[sound_name] = sound_obj
                    print(f"✓ ÄÄNITEHOSTE LADATTU: {category} - {sound_name}")
                except pygame.error as e:
                    print(f"❌ VIRHE ÄÄNITEHOSTE LATAAMISESSA {sound_path}: {e}")

    # ============================================================================
    # ÄÄNENVOIMAKKUUDEN SÄÄTÖ
    # ============================================================================

    def set_master_volume(self, volume):
        """
        ASETTAA PÄÄÄNENVOIMAKKUUDEN KAIKILLE ÄÄNILLE (MUSIIKKI + TEHOSTEET)
        
        PARAMETRI:
            volume (float): ÄÄNENVOIMAKKUUS 0.0 - 1.0 VÄLILLÄ
                           0.0 = ÄÄNI POIS, 1.0 = MAKSIMIÄÄNI
        """
        self.master_volume = max(0.0, min(1.0, volume))
        self._update_all_volumes()

    def set_sfx_volume(self, volume):
        """
        ASETTAA ÄÄNITEHOSTEIDEN ÄÄNENVOIMAKKUUDEN
        
        PARAMETRI:
            volume (float): ÄÄNENVOIMAKKUUS 0.0 - 1.0 VÄLILLÄ
        """
        self.sfx_volume = max(0.0, min(1.0, volume))
        self._update_all_volumes()

    def set_music_volume(self, volume):
        """
        ASETTAA TAUSTAMUSIIKAN ÄÄNENVOIMAKKUUDEN
        
        PARAMETRI:
            volume (float): ÄÄNENVOIMAKKUUS 0.0 - 1.0 VÄLILLÄ
        """
        self.music_volume = max(0.0, min(1.0, volume))
        self._update_music_volume()

    # ============================================================================
    # KATEGORIAKOHTAINEN ÄÄNENVOIMAKKUUDEN SÄÄTÖ
    # ============================================================================

    def set_weapons_volume(self, volume):
        """ASETTAA WEAPON-ÄÄNIEN ÄÄNENVOIMAKKUUDEN"""
        self.weapons_volume = max(0.0, min(1.0, volume))
        self._update_all_volumes()

    def set_enemy_actions_volume(self, volume):
        """ASETTAA ENEMY ACTION -ÄÄNIEN ÄÄNENVOIMAKKUUDEN"""
        self.enemy_actions_volume = max(0.0, min(1.0, volume))
        self._update_all_volumes()

    def set_boss_actions_volume(self, volume):
        """ASETTAA BOSS ACTION -ÄÄNIEN ÄÄNENVOIMAKKUUDEN"""
        self.boss_actions_volume = max(0.0, min(1.0, volume))
        self._update_all_volumes()

    def set_collisions_volume(self, volume):
        """ASETTAA COLLISION-ÄÄNIEN ÄÄNENVOIMAKKUUDEN"""
        self.collisions_volume = max(0.0, min(1.0, volume))
        self._update_all_volumes()

    def set_menu_volume(self, volume):
        """ASETTAA MENU-ÄÄNIEN ÄÄNENVOIMAKKUUDEN"""
        self.menu_volume = max(0.0, min(1.0, volume))
        self._update_all_volumes()

    def set_bombs_volume(self, volume):
        """ASETTAA BOMB-ÄÄNIEN ÄÄNENVOIMAKKUUDEN"""
        self.bombs_volume = max(0.0, min(1.0, volume))
        self._update_all_volumes()

    def set_sound_volume(self, sound_name, volume):
        """
        ASETTAA YKSITTÄISEN ÄÄNEN ÄÄNENVOIMAKKUUDEN
        KÄYTÖS: game_sounds.set_sound_volume("laser_fire", 0.5)
        
        PARAMETRIT:
            sound_name (str): ÄÄNEN NIMI (esim. "laser_fire", "boss_explosion")
            volume (float): ÄÄNENVOIMAKKUUS 0.0 - 1.0 VÄLILLÄ
        """
        if sound_name in self.INDIVIDUAL_SOUND_VOLUMES:
            self.INDIVIDUAL_SOUND_VOLUMES[sound_name] = max(0.0, min(1.0, volume))
            self._update_all_volumes()
            print(f"✓ {sound_name} äänenvoimakkuus asetettu: {volume*100:.0f}%")
        else:
            print(f"❌ VIRHE: Ääntä '{sound_name}' EI löydy INDIVIDUAL_SOUND_VOLUMES:sta")

    def get_sound_volume(self, sound_name):
        """
        PALAUTTAA YKSITTÄISEN ÄÄNEN NYKYISEN ÄÄNENVOIMAKKUUDEN
        KÄYTÖS: volume = game_sounds.get_sound_volume("laser_fire")
        
        PARAMETRI:
            sound_name (str): ÄÄNEN NIMI
        
        PALAUTTAA:
            float: ÄÄNENVOIMAKKUUS 0.0 - 1.0 VÄLILLÄ
        """
        return self.INDIVIDUAL_SOUND_VOLUMES.get(sound_name, 1.0)

    def get_all_volumes(self):
        """
        PALAUTTAA SANAKIRJAN KAIKISTA ÄÄNENVOIMAKKUUSASETUKSISTA
        KÄYTÖSSÄ Settings-menussa äänien tallentamiseen ja lataamiseen
        
        PALAUTTAA:
            dict: {
                "music_volume": float,
                "sfx_volume": float,
                "weapons_volume": float,
                "collisions_volume": float,
                "menu_volume": float,
                "enemy_actions_volume": float,
                "boss_actions_volume": float,
                "bombs_volume": float,
                "individual_sounds": {...}  # KAIKKI YKSITTÄISET ÄÄNET
            }
        """
        return {
            "music_volume": self.music_volume,
            "sfx_volume": self.sfx_volume,
            "weapons_volume": self.weapons_volume,
            "collisions_volume": self.collisions_volume,
            "menu_volume": self.menu_volume,
            "enemy_actions_volume": self.enemy_actions_volume,
            "boss_actions_volume": self.boss_actions_volume,
            "bombs_volume": self.bombs_volume,
            "individual_sounds": dict(self.INDIVIDUAL_SOUND_VOLUMES),
        }

    def set_all_volumes(self, volume_dict):
        """
        ASETTAA KAIKKI ÄÄNENVOIMAKKUUSARVOT SANAKIRJASTA
        KÄYTÖSSÄ Settings-menussa äänien lataamiseen tiedostosta
        
        PARAMETRI:
            volume_dict (dict): SANAKIRJA JOSSA AVAIMET = ÄÄNENVOIMAKKUUDEN NIMET, ARVOT = VOLUMET (0.0-1.0)
        """
        if "music_volume" in volume_dict:
            self.set_music_volume(volume_dict["music_volume"])
        if "sfx_volume" in volume_dict:
            self.set_sfx_volume(volume_dict["sfx_volume"])
        if "weapons_volume" in volume_dict:
            self.set_weapons_volume(volume_dict["weapons_volume"])
        if "collisions_volume" in volume_dict:
            self.set_collisions_volume(volume_dict["collisions_volume"])
        if "menu_volume" in volume_dict:
            self.set_menu_volume(volume_dict["menu_volume"])
        if "enemy_actions_volume" in volume_dict:
            self.set_enemy_actions_volume(volume_dict["enemy_actions_volume"])
        if "boss_actions_volume" in volume_dict:
            self.set_boss_actions_volume(volume_dict["boss_actions_volume"])
        if "bombs_volume" in volume_dict:
            self.set_bombs_volume(volume_dict["bombs_volume"])
        # LATAA MYÖS YKSITTÄISET ÄÄNET
        if "individual_sounds" in volume_dict:
            for sound_name, volume in volume_dict["individual_sounds"].items():
                self.set_sound_volume(sound_name, volume)

    def _update_all_volumes(self):
        """
        SISÄINEN METODI: PÄIVITTÄÄ KAIKKIEN ÄÄNIEN ÄÄNENVOIMAKKUUDEN
        OTTAA HUOMIOON:
        - PÄÄ-ÄÄNEN (master_volume)
        - EFEKTIÄÄN (sfx_volume)
        - KATEGORIAN ÄÄNENVOIMAKKUUDEN (weapons_volume, jne.)
        - YKSILÖLLISEN ÄÄNEN ÄÄNENVOIMAKKUUDEN (laser_fire = 0.6, jne.)
        """
        # PÄIVITÄ JOKAISEN ÄÄNITEHOSTE ÄÄNENVOIMAKKUUS
        for sound_name, sound_obj in self.sfx_dict.items():
            # ETSI KATEGORIAN ÄÄNENVOIMAKKUUS
            category = self.SOUND_CATEGORY_MAP.get(sound_name, "SFX")
            category_volume = getattr(self, f"{category.lower()}_volume", 1.0)
            
            # ETSI YKSILÖLLINEN ÄÄNEN ÄÄNENVOIMAKKUUS
            individual_volume = self.INDIVIDUAL_SOUND_VOLUMES.get(sound_name, 1.0)
            
            # LASKE LOPULLINEN ÄÄNENVOIMAKKUUS:
            # master * sfx * kategoria * yksilöllinen
            combined_volume = self.master_volume * self.sfx_volume * category_volume * individual_volume
            sound_obj.set_volume(combined_volume)

        # PÄIVITÄ MUSIIKIN ÄÄNENVOIMAKKUUS
        self._update_music_volume()

    def _update_music_volume(self):
        """
        SISÄINEN METODI: PÄIVITTÄÄ MUSIIKIN ÄÄNENVOIMAKKUUDEN
        OTTAA HUOMIOON PÄÄ-ÄÄNEN JA MUSIIKIN ÄÄNENVOIMAKKUUDEN
        """
        combined_music_volume = self.master_volume * self.music_volume
        pygame.mixer.music.set_volume(combined_music_volume)

    # ============================================================================
    # ÄÄNITEHOSTEIDEN TOISTO
    # ============================================================================

    def play_sfx(self, sound_name, loops=0):
        """
        TOISTAA ÄÄNITEHOSTEEN NIMEN PERUSTEELLA
        
        PARAMETRIT:
            sound_name (str): ÄÄNITEHOSTE NIMEN - HAETAAN SFX_DICT:STÄ
            loops (int): KUINKA MONTA KERTAA ÄÄNI TOISTETAAN LISÄKSI (OLETUS: 0 = KERRAN)
                        -1 = LOOPPI IKUISESTI
        
        POIKKEUS:
            KeyError: JOS ÄÄNITEHOSTETTA EI LÖYDY SANAKIRJASTA
        """
        if sound_name not in self.sfx_dict:
            print(f"❌ VIRHE: ÄÄNITEHOSTETTA '{sound_name}' EI LÖYDY")
            return

        sound = self.sfx_dict[sound_name]
        sound.play(loops=loops)

    def play_music(self, music_name, loops=-1, start=0.0):
        """
        TOISTAA TAUSTAMUSIIKKIA
        
        PARAMETRIT:
            music_name (str): MUSIIKIN NIMI - HAETAAN MUSIC_DICT:STÄ
            loops (int): KUINKA MONTA KERTAA MUSIIKKI TOISTETAAN (OLETUS: -1 = IKUISESTI)
                        0 = KERRAN, 1 = KAKSI KERTAA, JNE.
            start (float): SEKUNNISSA MISSÄ ALOITETAAN TOISTAMINEN (OLETUS: 0.0 = ALUSTA)
        
        POIKKEUS:
            FileNotFoundError: JOS MUSIIKKITIEDOSTOA EI LÖYDY
        """
        if music_name not in self.music_dict:
            print(f"❌ VIRHE: MUSIIKKIA '{music_name}' EI LÖYDY")
            return

        music_path = self.music_dict[music_name]

        # TARKISTA ETTÄ TIEDOSTO OIKEASTI ON OLEMASSA
        if not os.path.exists(music_path):
            raise FileNotFoundError(f"MUSIIKKITIEDOSTO PUUTTUU: {music_path}")

        try:
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.play(loops=loops, start=start)
            self.current_music = music_name
            self._update_music_volume()
            print(f"▶️  MUSIIKKI ALKOI: {music_name}")
        except pygame.error as e:
            print(f"❌ VIRHE MUSIIKIN TOISTAMISESSA: {e}")

    def stop_music(self, fadeout_ms=0):
        """
        PYSÄYTTÄÄ TAUSTAMUSIIKAN
        
        PARAMETRI:
            fadeout_ms (int): FADE-OUT AIKA MILLISEKUNTEISSA (OLETUS: 0 = VÄLITÖN PYSÄYTYS)
                            500 = 0.5 SEKUNTIA HÄIPYÄ ÄÄNI ENNEN PYSÄYTYSTÄ
        """
        if fadeout_ms > 0:
            pygame.mixer.music.fadeout(fadeout_ms)
        else:
            pygame.mixer.music.stop()

        self.current_music = None
        print("⏹️  MUSIIKKI PYSÄYTETTY")

    def stop_all_sounds(self):
        """
        PYSÄYTTÄÄ KAIKKI ÄÄNET VÄLITTÖMÄSTI - SEKÄ MUSIIKKI ETTÄ TEHOSTEET
        """
        pygame.mixer.music.stop()
        pygame.mixer.stop()
        self.current_music = None
        print("⏹️  KAIKKI ÄÄNET PYSÄYTETTY")

    # ============================================================================
    # ÄÄNEN HALLINTA JA TIETOJEN HAKEMINEN
    # ============================================================================

    def add_sound_effect(self, category, sound_name, file_path):
        """
        LISÄÄ UUDEN ÄÄNITEHOSTE LUOKKAAN AJON AIKANA
        HYÖDYLLINEN JOS HALUAT LISÄTÄ UUSIA ÄÄNIÄ JA PÄIVITTÄÄ KONFIGURAATIOTA
        
        PARAMETRIT:
            category (str): KATEGORIAN NIMI (EI KÄYTETÄ TALLENTELTUUN ETSINTÄÄN, VAIN INFO)
            sound_name (str): ÄÄNITEHOSTE NIMEN - TÄLLÄ NIMELLÄ ÄÄNELLÄ PYYDETÄÄN
            file_path (str): POLKU ÄÄNITIEDOSTOON
        
        POIKKEUS:
            FileNotFoundError: JOS ÄÄNITIEDOSTOA EI LÖYDY
            pygame.error: JOS ÄÄNTÄ EI VOI LADATA
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"ÄÄNITIEDOSTO PUUTTUU: {file_path}")

        try:
            sound_obj = pygame.mixer.Sound(file_path)
            self.sfx_dict[sound_name] = sound_obj
            print(f"✓ ÄÄNITEHOSTE LISÄTTY: {category} - {sound_name}")
        except pygame.error as e:
            print(f"❌ VIRHE ÄÄNITEHOSTE LATAAMISESSA {file_path}: {e}")
            raise

    def get_all_sound_names(self):
        """
        PALAUTTAA SANAKIRJAN JOKA SISÄLTÄÄ KAIKKI KÄYTETTÄVISSÄ OLEVAT ÄÄNET
        
        PALAUTTAA:
            dict: {"music": [MUSIIKKI NIMET], "sfx": [ÄÄNITEHOSTE NIMET]}
        """
        return {
            "music": list(self.music_dict.keys()),
            "sfx": list(self.sfx_dict.keys())
        }

    def is_music_playing(self):
        """
        TARKISTAA ONKO TAUSTAMUSIIKKI PARHAILLAAN KÄYNNISSÄ
        
        PALAUTTAA:
            bool: TRUE JOS MUSIIKKI SOI, FALSE JOS EI
        """
        return pygame.mixer.music.get_busy()

    def pause_music(self):
        """
        TAUOTTAA MUSIIKAN - SE JÄÄ SIIHEN KOHTAAN
        JATKA MUSIIKKIA RESUME_MUSIC() METODILLA
        """
        pygame.mixer.music.pause()
        print("⏸️  MUSIIKKI PAUSELLA")

    def resume_music(self):
        """
        JATKAA TAUOTETUN MUSIIKIN TOISTAMISTA EDELLISESTÄ KOHDASTA
        """
        pygame.mixer.music.unpause()
        print("▶️  MUSIIKKI JATKUU")

    # ============================================================================
    # OHJELMAN SULKEMINEN
    # ============================================================================

    def quit(self):
        """
        SULKEE PYGAME MIXERIN JA VAPAUTTAA RESURSSIT
        KUTSUTA ENNEN OHJELMAN SULKEMISTA
        """
        self.stop_all_sounds()
        pygame.mixer.quit()
        print("🔇 PYGAME MIXER SULJETTU")


# ================================================================================
# GLOBAALI SOUNDS-INSTANSSI - KÄYTÄ TÄTÄ PELISSÄ
# ================================================================================
# TÄMÄ ASETETAAN GameStateManager:issa, MUUT PELIN OSAT VOIVAT KÄYTTÄÄ SITÄ MALLILLA:
# from pelimusat import game_sounds
# if game_sounds:
#     game_sounds.play_sfx("laser_fire")
game_sounds = None


# ================================================================================
# TESTAUSOSIO - NÄYTÄ LUOKAN TOIMINTAA
# ================================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("PELIMUSAT - TESTAUSOSIO")
    print("="*80 + "\n")

    # ALUSTA PELIN ÄÄNIJÄRJESTELMÄ
    print("1️⃣  ALUSTETAAN PELIN ÄÄNIJÄRJESTELMÄ...")
    sounds = GameSounds()

    print("\n2️⃣  SAATAVILLA OLEVAT ÄÄNET:")
    all_sounds = sounds.get_all_sound_names()
    print(f"   MUSIIKKI: {all_sounds['music']}")
    print(f"   TEHOSTEET: {all_sounds['sfx']}")

    print("\n3️⃣  TESTATAAN ÄÄNENVOIMAKKUUDEN SÄÄTÖÄ...")
    sounds.set_master_volume(0.7)
    print("   ► PÄÄÄÄNI ASETETTU: 70%")

    sounds.set_sfx_volume(0.8)
    print("   ► TEHOSTEIDEN ÄÄNENVOIMAKKUUS: 80%")

    sounds.set_music_volume(0.6)
    print("   ► MUSIIKIN ÄÄNENVOIMAKKUUS: 60%")

    print("\n4️⃣  TESTATAAN ÄÄNITEHOSTEEN TOISTOA...")
    print("   ► TOISTETAAN: laser_fire")
    sounds.play_sfx("laser_fire")

    print("\n5️⃣  TESTATAAN MUSIIKIN TOISTOA...")
    print("   ► TOISTETAAN: pelimusa-root")
    sounds.play_music("pelimusa-root", loops=-1)

    import time
    time.sleep(2)

    print("\n6️⃣  TESTATAAN MUSIIKIN PAUSE/RESUME...")
    sounds.pause_music()
    time.sleep(1)
    sounds.resume_music()

    print("\n7️⃣  TESTATAAN UUDEN ÄÄNITEHOSTE LISÄÄMISTÄ...")
    try:
        # TÄMÄ EPÄONNISTUU KOSKA TIEDOSTOA EI OLE, MUTTA VIRHEENKÄSITTELY TOIMII
        sounds.add_sound_effect("EXPLOSIONS", "big_explosion", "Aanet/uusi-rajahdys.mp3")
    except FileNotFoundError:
        print("   ⚠️  TIEDOUSTOA EI LÖYTYNYT (ODOTETTUA)")

    print("\n8️⃣  TARKISTETAAN MUSIIKKI STATUS...")
    if sounds.is_music_playing():
        print("   ✓ MUSIIKKI ON KÄYNNISSÄ")
    else:
        print("   ✗ MUSIIKKI EI OLE KÄYNNISSÄ")

    print("\n9️⃣  PYSÄYTETÄÄN KAIKKI ÄÄNET...")
    sounds.stop_all_sounds()

    print("\n🔟  SULJETAAN ÄÄNIJÄRJESTELMÄ...")
    sounds.quit()

    print("\n" + "="*80)
    print("✓ TESTAUS VALMIS")
    print("="*80 + "\n")
