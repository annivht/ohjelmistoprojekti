"""
SaveGame moduuli - hallinnoi pelin tallentamista ja lataamista
Tallentaa: nykyinen level, aalto, pisteet, pelaajan tilan (health, ammo)
Tallennusformaatti: JSON
Tallennustiedosto: savegame.json
"""

import json
import os
from pathlib import Path


class SaveGameManager:
    """Hallinnoi pelin tallentamista ja lataamista JSON-formaatissa"""

    # Tallennustiedoston sijainti
    SAVEFILE_PATH = "savegame.json"

    @staticmethod
    def save_game(level_number: int, wave_number: int, total_score: int, 
                  player_health: int = 5, player_ammo_type1: int = 100, 
                  player_ammo_type2: int = 50, player_name: str = "Player") -> bool:
        """
        Tallentaa pelin tilan JSON-tiedostoon.
        
        Args:
            level_number: Nykyinen levelin numero (1-5)
            wave_number: Nykyinen aallon numero (1-4)
            total_score: Kerätyt pisteet
            player_health: Pelaajan nykyinen terveys
            player_ammo_type1: Ensimmäisen aseen ammo
            player_ammo_type2: Toisen aseen ammo
            player_name: Pelaajan nimi
            
        Returns:
            True jos tallennus onnistui, False muuten
        """
        try:
            save_data = {
                "level_number": int(level_number),
                "wave_number": int(wave_number),
                "total_score": int(total_score),
                "player_health": int(player_health),
                "player_ammo_type1": int(player_ammo_type1),
                "player_ammo_type2": int(player_ammo_type2),
                "player_name": str(player_name),
            }
            
            with open(SaveGameManager.SAVEFILE_PATH, 'w') as f:
                json.dump(save_data, f, indent=4)
            
            print(f"Peli tallennettu: Level {level_number}, Wave {wave_number}, Pisteet: {total_score}, HP: {player_health}")
            return True
            
        except Exception as e:
            print(f"Virhe pelin tallentamisessa: {e}")
            return False

    @staticmethod
    def load_game() -> dict or None:
        """
        Lataa tallennetun pelin tilan JSON-tiedostosta.
        
        Returns:
            Dict sisältäen (level_number, wave_number, total_score, player_health, 
            player_ammo_type1, player_ammo_type2, player_name) tai None jos ei tallennusta
        """
        try:
            if not os.path.exists(SaveGameManager.SAVEFILE_PATH):
                return None
            
            with open(SaveGameManager.SAVEFILE_PATH, 'r') as f:
                save_data = json.load(f)
            
            # Validoi tallennusdata
            required_keys = ["level_number", "wave_number", "total_score", "player_health", 
                           "player_ammo_type1", "player_ammo_type2", "player_name"]
            if not all(key in save_data for key in required_keys):
                print("Virheellinen tallennustiedosto")
                return None
            
            print(f"Peli ladattu: Level {save_data['level_number']}, Wave {save_data['wave_number']}, Pisteet: {save_data['total_score']}, HP: {save_data['player_health']}")
            return save_data
            
        except Exception as e:
            print(f"Virhe pelin lataamisessa: {e}")
            return None

    @staticmethod
    def has_savegame() -> bool:
        """Tarkistaa onko tallennustiedosto olemassa"""
        return os.path.exists(SaveGameManager.SAVEFILE_PATH)

    @staticmethod
    def delete_savegame() -> bool:
        """Poistaa tallennetun pelin"""
        try:
            if os.path.exists(SaveGameManager.SAVEFILE_PATH):
                os.remove(SaveGameManager.SAVEFILE_PATH)
                print("Tallennusdata poistettu")
                return True
            return False
        except Exception as e:
            print(f"Virhe tallennustiedon poistamisessa: {e}")
            return False
