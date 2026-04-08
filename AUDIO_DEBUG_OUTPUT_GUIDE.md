# ÄÄNIASETUKSIEN DIAGNOSTIIKKA - DEBUG OUTPUT GUIDE

## MITÄ KORJATTIIN

### 1. Ongelma: Settings-valikko ei lataa asetuksia takaisin
**Syy**: Kun `settings_menu_main()` palaan MainMenuState:iin, `set_state()` ei kutsua `on_enter()`:ia, joten `_load_audio_settings()` ei kutsua automaattisesti.

**Ratkaisu**: Lisättiin `self._load_audio_settings()` suoraan kun Settings-valikko sulkeutuu (MainMenuState.py rivi ~77).

### 2. Lisätty: Debug-output koko ketjuun
Paina: `python main.py` ja tuijoita konsoliin. Seuraavat tulosteet kertovat että järjestelmä toimii:

---

## ODOTETTU CONSOLE OUTPUT - KAAVION MUKAAN

### TEST SKENARIO: Avaa peli → Settings → Säädä ääniä → Palaa

```
[MAINMENU] ⚙️ Settings-nappia painettu
[MAINMENU] 📂 Avataan Settings-valikko...
[SETTINGS_CALLBACK] 🎵 Musiikin äänenvoimakkuus muuttui: 0.4 (40%)
[SETTINGS_CALLBACK] ✓ Asetettu peliin
[SETTINGS_CALLBACK] 📊 Menu data: {...'music_volume': 0.4, 'sfx_volume': 0.8...}
[SAVE_AUDIO] 💾 Tallennetaan audio_settings.json: Musiikki=40%, SFX=80%
[SAVE_AUDIO] ✅ TALLENNETTU ONNISTUNEESTI

[APPLY_SETTINGS] 🎮 Apply Settings painike painettu!
[APPLY_SETTINGS] 📊 Menu data: {...'music_volume': 0.4, 'sfx_volume': 0.8...}
[APPLY_SETTINGS] 🎵 Haetut äänenvoimakkuudet: Musiikki=40%, SFX=80%
[SAVE_AUDIO] 💾 Tallennetaan audio_settings.json: Musiikki=40%, SFX=80%
[SAVE_AUDIO] ✅ TALLENNETTU ONNISTUNEESTI
[APPLY_SETTINGS] ✅ ÄÄNENVOIMAKKUUS ASETETTU PELIIN - Musiikki: 40%, Tehosteet: 80%

[MAINMENU] 📂 Settings-valikko sulkeutui - Ladataan asetukset uudelleen
[MAINMENU] _load_audio_settings() ALOITETTU
[MAINMENU] 📂 Luetaan audio_settings.json
[MAINMENU] ✓ JSON LADATTU: {'music_volume': 0.4, 'sfx_volume': 0.8}
[MAINMENU] ✅ ÄÄNENVOIMAKKUUS ASETETTU - MUSIIKKI: 40%, TEHOSTEET: 80%
```

---

## MITÄ JOKAINEN VAIHE TARKOITTAA

| Output | Merkitys | OK/VIRHE |
|--------|----------|---------|
| `[SETTINGS_CALLBACK] 🎵` | Slider muuttui → callback kutsuttiin | ✅ OK |
| `[SETTINGS_CALLBACK] ✓ Asetettu peliin` | Ääni asetettu game_sounds objektiin | ✅ OK |
| `[SAVE_AUDIO] 💾 Tallennetaan` | JSON-tallennusta aloitetaan | ✅ OK |
| `[SAVE_AUDIO] ✅ TALLENNETTU` | Tiedosto kirjoitettu levylle | ✅ OK |
| `[APPLY_SETTINGS] 🎮` | Apply Settings nappi painettu | ✅ OK |
| `[MAINMENU] 📂 Settings-valikko sulkeutui` | Palataan Main Menuun | ✅ OK |
| `[MAINMENU] _load_audio_settings() ALOITETTU` | Load-funktio kutsuttiin | ✅ OK |
| `[MAINMENU] 📂 Luetaan audio_settings.json` | JSON-tiedostoa luetaan | ✅ OK |
| `[MAINMENU] ✓ JSON LADATTU` | Tiedosto avattu ja jäsennetty | ✅ OK |
| `[MAINMENU] ✅ ÄÄNENVOIMAKKUUS ASETETTU` | Asetukset asetettu peliin | ✅ OK |

---

## VIRHEITÄ - MITÄ ETSIÄ

### VIRHE 1: Callback ei ilmesty konsoliin
```
OLETUS: `[SETTINGS_CALLBACK] 🎵 Musiikin äänenvoimakkuus muuttui...`
NÄYTTÄÄ: Mitään ei ilmesty
SYYN: Slider callback ei kutsuttu. Tarkista:
  - Onko slideri olemassa? (range_slider widgets)
  - Onko onchange callback oikein yhdistetty?
  - Onko pelimusat.game_sounds None?
```

### VIRHE 2: Callback kutsuu mutta `[SAVE_AUDIO]` ei näy
```
NÄYTTÄÄ: `[SETTINGS_CALLBACK] ✓ Asetettu peliin`
MUTTA: `[SAVE_AUDIO]` ei ilmesty
SYY: save_audio_settings() ei kutsuttu callbackissa
TARKISTA: Onko try-except estänyt koodin? Onko general_menu.get_input_data() epäonnistunut?
```

### VIRHE 3: Apply Settings ei kutsua save_audio_settings
```
NÄYTTÄÄ: `[APPLY_SETTINGS] 🎮 Apply Settings painike painettu!`
MUTTA: `[SAVE_AUDIO] 💾` ei ilmesty
SYYN: apply_display_settings_from_menu() ei suorita save_audio_settings() kutsua
TARKISTA: Onko funktio olemassa ja kutsutaan?
```

### VIRHE 4: Settings-valikko sulkeutuu mutta `_load_audio_settings()` ei kutsutaan
```
NÄYTTÄÄ: `[MAINMENU] 📂 Settings-valikko sulkeutui - Ladataan asetukset uudelleen`
MUTTA: `[MAINMENU] _load_audio_settings() ALOITETTU` ei ilmesty
SYYN: MainMenuState line ~77 kutsua `self._load_audio_settings()` ei ole!
TARKISTA: Onko funktio lisätty settings-action jäljeen?
```

### VIRHE 5: _load_audio_settings() kutsuu mutta audio_settings.json ei löydy
```
NÄYTTÄÄ: `[MAINMENU] _load_audio_settings() ALOITETTU`
MUTTA: `[MAINMENU] ⚠️ audio_settings.json EI OLE OLEMASSA`
SYYN: Tiedosto ei ole vielä luotu!
RATKAISU: 
  1. Säädä äänenvoimakkuutta slidereilla → tulisi luoda json
  2. Paina Apply Settings → tulisi luoda json
  3. Tarkista että save_audio_settings() kirjoittaa tiedostoon
```

### VIRHE 6: JSON ladataan mutta asetukset eivät asetu peliin
```
NÄYTTÄÄ: `[MAINMENU] ✓ JSON LADATTU: {'music_volume': 0.4, ...}`
MUTTA: `[MAINMENU] ❌ manager tai sounds on None!` 
SYYN: Jossakin kohdin manager tai game_sounds on None
TARKISTA: Onko GameStateManager.sounds asetettu oikein?
```

---

## TEST PROTOCOL

### TEST 1: Perustallennus ja paluu
```bash
python main.py

1. Paina Settings → odota että näet "[MAINMENU] ⚙️ Settings-nappia painettu"
2. Säädä Music Volume → 30% 
   ODOTA: "[SETTINGS_CALLBACK] 🎵 Musiikin äänenvoimakkuus muuttui: 0.3"
3. Paina Apply Settings
   ODOTA: "[APPLY_SETTINGS] ✅ ÄÄNENVOIMAKKUUS ASETETTU"
4. Paina Back
   ODOTA: "[MAINMENU] ✅ ÄÄNENVOIMAKKUUS ASETETTU - MUSIIKKI: 30%"
5. Tarkista audio_settings.json → sisällös: {"music_volume": 0.3, ...}
```

### TEST 2: Slider defaults Settings-valikossa
```bash
1. Paina Settings uudelleen
2. Tarkista sliderit VISUAALISESTI
   - Music Volume slider pitäisi olla 30% (edellisestä testista)
   - JOS on 80% → Slider default ei asetu oikein
```

### TEST 3: Suljetaan peli ja avataan uudelleen
```bash
1. Suljetaan peli
2. python main.py uudelleen
3. ODOTA: "[MAINMENU] on_enter() KUTSUTTU"
4. ODOTA: "[MAINMENU] ✅ ÄÄNENVOIMAKKUUS ASETETTU - MUSIIKKI: 30%"
   - Jos tämä ei näy → asetukset eivät säily pelien välillä
```

---

## CONSOLE OUTPUT FILTERING

Konsoliin tulee paljon outputia, joten voit filtteröidä debug-rivejä:

```bash
# Näytä vain ääniasetuksiin liittyvää
python main.py | grep -i "AUDIO\|CALLBACK\|MAINMENU\|SETTINGS\|ÄÄNENVOIMAKKUUS"

# Nayta vain virheet
python main.py | grep -i "ERROR\|VIRHE\|❌"

# Näytä vain onnistumiset
python main.py | grep -i "✅\|ONNISTUNEESTI"
```

---

## SEURAAVA ASKELE

Kun korjaus on valmis ja testi läpi menee:
1. Poista kaikki `print(f"[DEBUG]...")` rivit
2. Tarkista että asetukset todella pysyvät
3. Tarkista että sliderit näyttävät oikeat arvot Settings-valikossa
