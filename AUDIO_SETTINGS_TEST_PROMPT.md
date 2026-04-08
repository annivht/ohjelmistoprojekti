# ÄÄNIASETUKSIEN TESTAUS - TÄYDELLINEN PROMPTI

## TESTIOHJEET: Varmista että äänenvoimakkuus-asetukset tallentuvat ja säilyvät

### TESTI 1: Perustallennus
**Tavoite**: Tarkista että asetukset tallentuvat audio_settings.json-tiedostoon

1. Avaa peli: `python main.py`
2. Mene Settings-valikkoon
3. Säädä "Music Volume" (esim. 40%) ja "Sound Effects Volume" (esim. 60%)
4. **TARKISTA KONSOLI**:
   - Pitäisi näkyä: `ÄÄNENVOIMAKKUUS ASETETTU - Musiikki: 40%, Tehosteet: 60%`
   - Tämä tarkoittaa että `on_music_volume_change()` tai `on_sfx_volume_change()` callback toimi
5. **TARKISTA TIEDOSTO**:
   - Avaa `audio_settings.json` -tiedosto
   - Pitäisi sisältää: `{"music_volume": 0.4, "sfx_volume": 0.6}`
   - **JOS EI**: Slider callback ei kaikki tallenna oikein

---

### TESTI 2: Apply Settings painike
**Tavoite**: Tarkista että "Apply Settings" tallentaa asetukset uudelleen

1. Settings-valikossa: Säädä "Music Volume" → 30%
2. Paina "Apply Settings" -nappia
3. **TARKISTA KONSOLI**:
   - Pitäisi näkyä: `ÄÄNENVOIMAKKUUS TALLENNETTU - Musiikki: 30%, Tehosteet: (nykyinen %)`
   - Tämä tarkoittaa että `apply_display_settings_from_menu()` toimi
4. **TARKISTA TIEDOSTO**:
   - `audio_settings.json` pitäisi sisältää: `{"music_volume": 0.3, ...}`

---

### TESTI 3: Palaavan Main Menu (KRIITTINEN)
**Tavoite**: Tarkista että palaava Main Menu lataa asetukset oikein

1. Settings-valikossa: Säädä "Music Volume" → 25%
2. Paina "Apply Settings"
3. Paina "Back" → palaa Main Menuun
4. **TARKISTA ÄÄNENVOIMAKKUUS**:
   - Musiikin pitäisi soida **25% äänenvoimakkuudella** (ei 80% defaultilla!)
   - **JOS SOI 80%**: MainMenuState.on_enter() EI lataa asetuksia oikein
5. **TARKISTA KONSOLI**:
   - Tulisi näkyä: `ÄÄNENVOIMAKKUUS LADATTU - Musiikki: 25%, Tehosteet: X%`

---

### TESTI 4: Settings-valikko uudestaan (SLIDER DEFAULTS)
**Tavoite**: Tarkista että slidereille asetetaan oikeat default-arvot

1. Avaa Settings-valikon uudelleen
2. **TARKISTA SLIDERIT VISUAALISESTI**:
   - "Music Volume" slider pitäisi näyttää **25%** (edellisestä testista)
   - "Sound Effects Volume" slider pitäisi näyttää mitä se oli
   - **JOS NÄYTTÄVÄT 80%**: Slidereille ei aseteta oikea `default=audio_data.get()` arvo

---

### TESTI 5: Kokonaisketju
**Tavoite**: Kaikki toimivat yhdessä

1. `python main.py`
2. Settings → "Music Volume" → 50%, "SFX Volume" → 70% → Apply Settings
3. Palaa Main Menuun → Tarkista että ääni on 50%/70%
4. Settings uudelleen → Tarkista että sliderit näyttävät 50%/70%
5. Säädä → 20%/80% → Apply Settings
6. Palaa → Tarkista 20%/80%
7. Sulje peli ja avaa uudelleen: `python main.py`
   - **Pitäisi käynnistyä 20%/80% äänivoimakkuudella**

---

## TODENNÄKÖISET ONGELMAT

### ONGELMA 1: "Asetukset eivät tallennu sliderin muuttuessa"
- **Syy**: `on_music_volume_change()` tai `on_sfx_volume_change()` callback ei toimi
- **Tarkista**:
  - Onko `pelimusat.game_sounds` None?
  - Palauttaako `general_menu.get_input_data()` oikeat arvot?
  - Tallentuuko `save_audio_settings()` JSON-tiedostoon?

### ONGELMA 2: "Paluu Main Menuun = ääni palaa defaultiin"
- **Syy**: `MainMenuState.on_enter()` ei kutsua `_load_audio_settings()`
- **Tarkista**:
  - Kutsutaanko `GameStateManager.set_state()` → `state.on_enter()`?
  - Onko `MainMenuState.on_enter()` määritelty?
  - Kutsutaanko `_load_audio_settings()` sieltä?

### ONGELMA 3: "Sliderit näyttävät väärät arvot Settings-valikossa"
- **Syy**: `audio_data = load_audio_settings()` ei lataa tuoreinta dataa
- **Tarkista**:
  - Kutsutaanko `load_audio_settings()` kun valikoita luodaan?
  - Tallentuuko `audio_data` ja käytetäänkö sitä `default=` parametrissa?

### ONGELMA 4: "Apply Settings painike ei tallenna"
- **Syy**: `apply_display_settings_from_menu()` ei kutsuta tai se ei toimi
- **Tarkista**:
  - Kutsutaanko `save_audio_settings()` siellä?
  - Palauttaako `general_menu.get_input_data()` oikeat arvot?

---

## VIRHEENJÄLJITYS

Lisää nämä print-lauseet tarkistukseksi:

### SettingsMenu.py - on_music_volume_change:
```python
def on_music_volume_change(value):
    print(f"[CALLBACK] on_music_volume_change: {value}")
    if pelimusat.game_sounds:
        pelimusat.game_sounds.set_music_volume(value)
    data = general_menu.get_input_data()
    print(f"[CALLBACK] menu data: {data}")
    try:
        sfx_vol = float(data.get("sfx_volume", 0.8))
        save_audio_settings(value, sfx_vol)
        print(f"[CALLBACK] TALLENNETTU: Music={value}, SFX={sfx_vol}")
    except (ValueError, TypeError) as e:
        print(f"[CALLBACK] VIRHE: {e}")
```

### MainMenuState.py - on_enter:
```python
def on_enter(self):
    print(f"[STATE] MainMenuState.on_enter() kutsuttu")
    self._load_audio_settings()
```

### MainMenuState.py - _load_audio_settings:
```python
def _load_audio_settings(self):
    print(f"[STATE] _load_audio_settings() aloitettu")
    audio_file = "audio_settings.json"
    if not os.path.exists(audio_file):
        print(f"[STATE] audio_settings.json EI OLE OLEMASSA")
        return
    ...
    print(f"[STATE] LADATTU JA ASETETTU: {music_vol}/{sfx_vol}")
```

---

## TESTIN LOPUSSA

Kun kaikki testit menevät läpi:
- ✅ Sliderit muuttuvat → tallennetaan JSON:iin suoraan
- ✅ Apply Settings painike → tallennetaan uudelleen
- ✅ Paluu Main Menuun → äänet pysyvät samoina (ei palaa defaultiin)
- ✅ Settings uudelleen → sliderit näyttävät oikeat arvot
- ✅ Pelin sulkeminen/avaaminen → äänet säilyvät
