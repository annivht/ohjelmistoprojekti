# Meteoriittijärjestelmän Toteutus - PÄIVITETTY

## Muutokset
Meteoriittijärjestelmä päivitetty kolmitasoiseksi:
- **MainMeteorite (100%)**: Iso meteoriitti, hajoaa 4x50% meteoriiteiksi
- **Meteor (50%)**: Keskikokoinen meteoriitti, hajoaa 2x25% pienemmäksi meteoriksi  
- **SmallMeteorite (25%)**: Pieni meteoriitti, ei hajoa

## Luodut Tiedostot

### Meteor/ kansion tiedostot

1. **meteor.py** - Kolme meteoriitti-luokkaa
   - `MainMeteorite` (100% koko, Meteor_01.png)
   - `Meteor` (50% koko, Meteor_05.png) 
   - `SmallMeteorite` (25% koko, Meteor_10.png)
   - Jokainen on ammuttavissa ja hajoaa osiksi

2. **meteor_helpers.py** - Spawnaamisapu-funktiot
   - `spawn_moving_meteor(game, speed=80, use_main=True)` - Spawnaa meteoriitti-klusterin
   - `spawn_meteor(game, x, y, image=None, meteor_type="medium")` - Spawnaa yksittäisen meteoriitin

3. **__init__.py** - Paketin alustus
   - Vie kaikki kolme meteoriitti-luokkaa

## Ydinpelin Integraatio

**Muutettu RocketGame.py:**
- Tuonti: `from Meteor.meteor import Meteor, MainMeteorite, SmallMeteorite`
- Meteoriitin päivitys: `meteor.update(self.dt)` pääsilmukassa
- **Ammuksien törmäys meteoriin:**
  - Tarkistetaan is_meteor ja health-attribuutit
  - Vähentää health 1
  - Kun health <= 0: kutsuu `get_fragments()` ja spawnaa pienempiä meteoreja
- Poistetaan kuolleet meteorit (`m.dead == True`)

## Meteoreiden Käyttäytyminen

### MainMeteorite (100%)
✅ Koko: ~300×300 pikseliä  
✅ Vauriot pelaajalle: 2 HP per törmäys  
✅ Ammuttavissa: Hajoaa 4 meteoriiteiksi (50%)  
✅ Kuva: Meteor_01.png  

### Meteor (50%)
✅ Koko: ~150×150 pikseliä  
✅ Vauriot pelaajalle: 1 HP per törmäys  
✅ Ammuttavissa: Hajoaa 2 pienemmäksi meteoriksi (25%)  
✅ Kuva: Meteor_05.png  

### SmallMeteorite (25%)
✅ Koko: ~75×75 pikseliä  
✅ Vauriot pelaajalle: 1 HP per törmäys  
✅ Ammuttavissa: Katoaa (ei hajoa edelleen)  
✅ Kuva: Meteor_10.png  

## Fragmentaation Järjestys

```
MainMeteorite (100%)
  ↓ (ammotetaan)
  4x Meteor (50%)
    ↓ (jokainen ammotaan)
    2x SmallMeteorite (25%)
      ↓ (ammotaan)
      Katoaa
```

## Meteoreiden Käyttö Tasoissa

### Perusesimerkki
```python
# Tasot/Taso1.py tai muissa tasoissa
from Meteor.meteor_helpers import spawn_moving_meteor

def spawn_wave_tasox(game, wave_num, ...):
    if wave_num == 1:
        # Spawnaa iso meteoriitti-klusteri
        spawn_moving_meteor(game, speed=150, use_main=True)
        return True
    return False
```

### Vaikeustaso Säätö
```python
# Iso meteoriitti (vaikeampi)
spawn_moving_meteor(game, speed=150, use_main=True)

# Keskikokoinen meteoriitti (normaali)
spawn_moving_meteor(game, speed=150, use_main=False)
```

## Kuvat

Käytetään Space-Shooter_objects setistä:
- `images/Space-Shooter_objects/PNG/Meteors/Meteor_01.png` → MainMeteorite
- `images/Space-Shooter_objects/PNG/Meteors/Meteor_05.png` → Meteor  
- `images/Space-Shooter_objects/PNG/Meteors/Meteor_10.png` → SmallMeteorite

## Testatut Ominaisuudet

✅ Meteorit latautuvat oikein  
✅ Fragmentaatio toimii ammuksilla  
✅ Törmäyslogiiikka toimii  
✅ Kokoluokat piirtyvät  
✅ Health-järjestelmä ja hajoaminen  

## Muutetut Tiedostot

- `RocketGame.py` - Ammuksien fragmentaatiologiikka lisätty
- `Meteor/meteor.py` - Kolme uutta luokkaa
- `Meteor/meteor_helpers.py` - Päivitetty spawn-funktiot
- `Meteor/__init__.py` - Vie kaikki luokat

