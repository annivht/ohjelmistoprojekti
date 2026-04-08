# ÄÄNIASETUKSIEN JÄRJESTELMÄ - TÄYDELLINEN KUVAUS

## ONGELMA JA RATKAISU

### Alkuperäinen ongelma
- **Käyttäjän ilmoitus**: "Kun painaa return to main menu äänet palaavat default tasolle"
- **Syy**: Settings-valikko sulkeutuessa `on_enter()` ei kutsutaan, joten `_load_audio_settings()` ei lataa JSON-asetuksia
- **Ratkaisu**: Lisätty `self._load_audio_settings()` suoraan Settings-valikko sulkemisen yhteydessä

---

## ARKKITEHTUURI

### 1. TIEDOSTOT JOTKA HALLITSEVAT ÄÄNIASETUKSIA

#### audio_settings.json (TALLENNUSTIEDOSTO)
```json
{
  "music_volume": 0.8,
  "sfx_volume": 0.8
}
```
- **Sijainti**: Projektin juuressa
- **Luodaan**: Kun käyttäjä ensimmäisen kerran tallentaa asetuksia
- **Päivitetään**: Jokaisen kerran kun slider muuttuu tai Apply Settings painetaan

#### MainMenuState.py (ASETUKSIEN LATAUS)
```
on_enter() → _load_audio_settings()
  ↓
  Lukee audio_settings.json
  ↓
  Asettaa pelimusat.game_sounds.set_music_volume()
  ↓
  Asettaa pelimusat.game_sounds.set_sfx_volume()
```

#### SettingsMenu.py (KÄYTTÖLIITTYMÄ)
```
Sliderit (Music Volume, SFX Volume)
  ↓
  on_music_volume_change() / on_sfx_volume_change() callbackit
  ↓
  save_audio_settings() JSON kirjoitukseen
  ↓
  Apply Settings nappi → apply_display_settings_from_menu()
```

#### pelimusat.py (ÄÄNI ENGINE)
```
game_sounds = GameSounds()
  ↓
  set_music_volume(value) asettaa pygame.mixer volumet
  ↓
  soittaa musiikkia loopissa
```

---

## PROSESSI: ASKELEITTAIN

### Vaihe 1: Peli käynnistyy
```
main.py
  ↓
GameStateManager.__init__()
  ↓
load_audio_settings() (FROM GameStateManager)
  ↓
GameSounds.set_music_volume()
GameSounds.set_sfx_volume()
  ↓
play_music("pelimusa-root", loops=-1)
```

### Vaihe 2: Käyttäjä avaa Settings-valikko
```
MainMenuState.handle_action("settings")
  ↓
settings_menu_main() (Valikot/SettingsMenu.py)
  ↓
sliderit näyttävät arvot audio_data:sta:
  "music_volume": load_audio_settings().get("music_volume", 0.8)
```

### Vaihe 3: Käyttäjä säätää slideria
```
Slider muuttuu (esim. 0.8 → 0.5)
  ↓
on_music_volume_change(0.5)
  ↓
game_sounds.set_music_volume(0.5)
  ↓
save_audio_settings(0.5, nykyinen_sfx)
  ↓
audio_settings.json kirjoitetaan levylle
```

### Vaihe 4: Käyttäjä painaa Apply Settings
```
apply_display_settings_from_menu()
  ↓
data = general_menu.get_input_data()
  ↓
music_volume = data.get("music_volume", 0.8)
sfx_volume = data.get("sfx_volume", 0.8)
  ↓
save_audio_settings(music_volume, sfx_volume)
  ↓
game_sounds.set_music_volume(music_volume)
game_sounds.set_sfx_volume(sfx_volume)
```

### Vaihe 5: Käyttäjä palaa Main Menuun (KRIITTINEN OSA - KORJATTU)
```
settings_menu_main() palaa Noneksi
  ↓
MainMenuState.handle_action() jatkaa
  ↓
self._load_audio_settings() ← UUSI RIVI (KORJAUS)
  ↓
Luetaan audio_settings.json
  ↓
game_sounds.set_music_volume()
game_sounds.set_sfx_volume()
```

### Vaihe 6: Käyttäjä palaa Settings-valikkoon
```
sliderit ladataan uudelleen audio_data:sta
  ↓
load_audio_settings() kutsutaan create_menus():ssä
  ↓
slidereille asetetaan default=audio_data.get("music_volume", 0.8)
```

---

## OSAT JA NIIDEN ROOLIT

### MainMenuState.py
**Kun päävalikkoon tullaan:**
- `on_enter()` kutsuu `_load_audio_settings()`
- Tämä tapahtuu pelin käynnistymisen yhteydessä

**Kun Settings-valikosta palataan:**
- `handle_action("settings")` kutsuu `settings_menu_main()`
- Heti perään kutsua `self._load_audio_settings()` ← KORJAUS
- Tämä varmistaa että asetukset ladataan JSON:ista

### SettingsMenu.py (Valikot/SettingsMenu.py)
**Slider widgets:**
- `range_slider` Music Volume (default=audio_data.get("music_volume", 0.8))
- `range_slider` SFX Volume (default=audio_data.get("sfx_volume", 0.8))

**Callback functions:**
- `on_music_volume_change()` - Kutsutaan JOKAISEN kerran kun slider muuttuu
  - Asettaa äänenvoimakkuuden peliin
  - Tallentaa asetukset JSON:iin
- `on_sfx_volume_change()` - Sama SFX-volyymille

**Apply Settings nappi:**
- `apply_display_settings_from_menu()` - Kutsutaan NAPPIA painettaessa
  - Hakee slidejen arvot
  - Tallentaa asetukset JSON:iin
  - Asettaa äänenvoimakkuuden peliin

### load_audio_settings()
**Kahdeta kertaa kutsutaan:**
1. GameStateManager.__init__() - pelin käynnistyessä
2. SettingsMenu.create_menus() - sliderit asetetaan

**Tekee:**
- Lukee audio_settings.json (jos olemassa)
- Palauttaa dict: `{"music_volume": float, "sfx_volume": float}`
- Jos tiedosto ei ole tai virhe → palauttaa `{"music_volume": 0.8, "sfx_volume": 0.8}`

### save_audio_settings(music_vol, sfx_vol)
**Kutsutaan:**
1. Slider callback (on_music_volume_change, on_sfx_volume_change)
2. Apply Settings nappi (apply_display_settings_from_menu)

**Tekee:**
- Kirjoittaa JSON:ia levylle
- `audio_settings.json`: `{"music_volume": music_vol, "sfx_volume": sfx_vol}`

---

## KRIITTISET KOHDAT

### KO #1: Slideille täytyy asetta oikeat default-arvot
```python
general_menu.add.range_slider(
    title="Music Volume",
    default=audio_data.get("music_volume", 0.8),  # ← KRIITTINEN
    ...
)
```
**JOS EPÄONNISTUU**: Sliderit näyttävät aina 80% vaikka asetukset olisivat eri

### KO #2: Settings-valikosta palaavat asetuksien täytyy latautua
```python
settings_action = settings_menu_main()
self._load_audio_settings()  # ← KRIITTINEN (LISÄTTY KORJAUKSENA)
```
**JOS EPÄONNISTUU**: Äänet palautuvat defaultiin päävalikkoon palatessa

### KO #3: JSON-tiedosto täytyy kirjoittaa onnistuneesti
```python
save_audio_settings(music_volume, sfx_volume)
```
**JOS EPÄONNISTUU**: Asetukset eivät tallennu pelin sulkemisen jälkeen

### KO #4: GameStateManager täytyy kutsua on_enter()
```python
if hasattr(self.state, 'on_enter'):
    self.state.on_enter()  # ← Kutsuu MainMenuState.on_enter()
```
**JOS EPÄONNISTUU**: Asetukset eivät lataudu pelin käynnistymisen yhteydessä

---

## DEBUG PRINT LOKITUKSET

Jokainen tärkeä vaihe on varustettu debug-printillä:

```
[MAINMENU] ⚙️ Settings-nappia painettu
[MAINMENU] _load_audio_settings() ALOITETTU
[MAINMENU] 📂 Luetaan audio_settings.json
[MAINMENU] ✓ JSON LADATTU: {...}
[MAINMENU] ✅ ÄÄNENVOIMAKKUUS ASETETTU - MUSIIKKI: 50%, TEHOSTEET: 80%

[SETTINGS_CALLBACK] 🎵 Musiikin äänenvoimakkuus muuttui: 0.5
[SAVE_AUDIO] 💾 Tallennetaan audio_settings.json: Musiikki=50%, SFX=80%
[SAVE_AUDIO] ✅ TALLENNETTU ONNISTUNEESTI

[APPLY_SETTINGS] 🎮 Apply Settings painike painettu!
[APPLY_SETTINGS] ✅ ÄÄNENVOIMAKKUUS ASETETTU PELIIN
```

---

## TARKISTUSLISTA

- [x] audio_settings.json luodaan ensimmäisellä tallennuksella
- [x] JSON päivittyy jokaisen sliderin muutoksen yhteydessä
- [x] Slider callbackit kutsuvat save_audio_settings()
- [x] Apply Settings painike kutsuu save_audio_settings()
- [x] MainMenuState._load_audio_settings() kutsutaan päävalikkoon tulessa
- [x] MainMenuState._load_audio_settings() kutsutaan Settings-valikosta palattaessa
- [x] Sliderit näyttävät oikeat default-arvot Settings-valikossa
- [x] Asetukset asetetaan game_sounds objektiin
- [x] Kaikilla on listattu oikeat poikkeukset (ei "except Exception")
- [x] Debug-print lokitukset dokumentoitu

---

## SEURAAVAT TESTAUKSET

Suorita nämä testit varmistaksesi että kaikki toimii:

### Test 1: Perusfunktionaalisuus
```bash
python main.py
→ Paina Settings
→ Säädä Music Volume → 30%
→ Paina Apply Settings
→ Paina Back
→ Tarkista että musiikki soii 30:llä äänenvoimakkuudella
```

### Test 2: Slider defaults
```bash
Paina Settings → Tarkista että slider näyttää 30% (edellisestä testista)
```

### Test 3: Pelin sulkeminen ja avaaminen
```bash
Sulje peli
Avaa uudelleen
Musiikki pitäisi soida 30% äänenvoimakkuudella
```

### Test 4: Useita muutoksia
```bash
Settings → Music 50%, SFX 70% → Apply → Back
Settings → Music 20%, SFX 90% → Apply → Back
...
Tarkista että kaikki asetukset säilyvät
```

---

## YHTEENVETO

**Korjauksen ydin:**
Kun Settings-valikko sulkeutuu, kutsutaan heti `self._load_audio_settings()` MainMenuState:issa. Tämä varmistaa että:
1. JSON-tiedosto luetaan
2. Asetukset asetetaan pelin äänijärjestelmään
3. Käyttäjä kuulee oikeat äänenvoimakkuudet päävalikossa

**Prosessi on nyt:**
1. Settings avautuu + sliderit saavat oikeat arvot JSON:ista ✅
2. Käyttäjä säätää slidereita → tallennetaan JSON:iin ✅
3. Käyttäjä painaa Apply Settings → tallennetaan JSON:iin ✅
4. Käyttäjä painaa Back → ladataan JSON:ista + asetetaan peliin ✅
