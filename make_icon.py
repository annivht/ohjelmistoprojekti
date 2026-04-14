"""
Muuntaa boost_5.png suoraan .ico-kuvakkeeksi
"""

from PIL import Image
from pathlib import Path


def create_boost_icon():
    """Käyttää boost_5.png:ää suoraan kuvakkeena"""
    
    project_root = Path(__file__).parent
    source_image = project_root / "alukset" / "FIGHTER-SPRITES" / "Boost1" / "Boost_5.png"
    icon_path = project_root / "build" / "game_icon.ico"
    
    icon_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading: {source_image}")
    
    # Avaa ja muuta 256x256
    img = Image.open(source_image).convert("RGBA")
    img_resized = img.resize((256, 256), Image.Resampling.LANCZOS)
    
    # Tallenna kaikissa kooissa
    img_resized.save(icon_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
    
    print(f"Icon saved: {icon_path}")
    print(f"Size: {icon_path.stat().st_size} bytes")


if __name__ == "__main__":
    create_boost_icon()
