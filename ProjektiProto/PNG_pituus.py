from PIL import Image
import os

def sprite_length(image_path):
    img = Image.open(image_path).convert("RGB")
    width, height = img.size
    y = height // 2  # keskikohta pystysuunnassa
    for x in range(width):
        r, g, b = img.getpixel((x, y))
        if (r, g, b) == (0, 0, 0):
            return x
    return None

def main():
    folder = r"C:\Users\juhok\Documents\1._Opinnot\1.KEVAT2026\Ohjelmistoprojekti\Github_kansio\ohjelmistoprojekti\alukset\alus\Corvette\Move"
    for filename in os.listdir(folder):
        if filename.lower().endswith(".png"):
            path = os.path.join(folder, filename)
            length = sprite_length(path)
            if length is not None:
                print(f"{filename}: pituus perästä ääriviivaan = {length} px")
            else:
                print(f"{filename}: ääriviivaa ei löytynyt")

if __name__ == "__main__":
    main()
# tällä scriptillä tarkistetaan mitta spriten perästä aluksen perään.

from PIL import Image

def sprite_length(image_path):
    img = Image.open(image_path).convert("RGB")
    width, height = img.size
    y = height // 2  # keskikohta pystysuunnassa

    # Aloitetaan perästä (vasemmalta)
    for x in range(width):
        r, g, b = img.getpixel((x, y))
        # Musta ääriviiva: RGB (0,0,0)
        if (r, g, b) == (0, 0, 0):
            print(f"Spriten pituus perästä ääriviivaan: {x} pikseliä")
            return x
    print("Ääriviivaa ei löytynyt.")
    return None
