# PSD-spritelistien automaattinen pilkkominen ja offset-laskenta
# Käyttää psd-tools-kirjastoa layerien ja/tai sprite sheetin lukemiseen
# HUOM: Asenna ensin psd-tools: pip install psd-tools

import os
from PIL import Image
from psd_tools import PSDImage

def extract_reference_patch(img, patch_size=10):
    width, height = img.size
    x0 = width - 15
    y0 = height // 2 - patch_size // 2
    patch = []
    for dy in range(patch_size):
        row = []
        for dx in range(patch_size):
            px = x0 + dx
            py = y0 + dy
            if 0 <= px < width and 0 <= py < height:
                row.append(img.getpixel((px, py)))
            else:
                row.append((0,0,0))
        patch.append(row)
    return patch, x0, y0

def patch_distance(patch1, patch2):
    dist = 0
    for y in range(len(patch1)):
        for x in range(len(patch1[0])):
            r1,g1,b1 = patch1[y][x]
            r2,g2,b2 = patch2[y][x]
            dist += (r1-r2)**2 + (g1-g2)**2 + (b1-b2)**2
    return dist

def find_best_patch_xy(img, ref_patch):
    width, height = img.size
    patch_size = len(ref_patch)
    best_x = 0
    best_y = 0
    best_dist = float('inf')
    for y0 in range(0, height - patch_size + 1):
        for x0 in range(0, width - patch_size + 1):
            patch = []
            for dy in range(patch_size):
                row = []
                for dx in range(patch_size):
                    px = x0 + dx
                    py = y0 + dy
                    row.append(img.getpixel((px, py)))
                patch.append(row)
            d = patch_distance(ref_patch, patch)
            if d < best_dist:
                best_dist = d
                best_x = x0
                best_y = y0
    return best_x, best_y

def get_all_layers(psd):
    """Palauttaa kaikki näkyvät layereiden lapset (myös groupien sisältä)."""
    layers = []
    def recurse(layer, depth=0):
        indent = '  ' * depth
        print(f"{indent}- {layer.name} (visible={layer.is_visible()}, has_pixels={layer.has_pixels()})")
        if hasattr(layer, 'layers') and layer.layers:
            for l in layer.layers:
                recurse(l, depth+1)
        else:
            if layer.is_visible() and layer.has_pixels():
                layers.append(layer)
    for l in psd:
        recurse(l)
    print(f"Löytyi {len(layers)} layeria, joissa on pikseleitä ja jotka ovat näkyvissä.")
    return layers

def process_psd_layers(psd_path, patch_size=10):
    psd = PSDImage.open(psd_path)
    # Oletetaan: ensimmäinen layer on referenssi (Idle), muut damage-spritet
    layers = get_all_layers(psd)
    if len(layers) < 2:
        print(f"PSD {psd_path}: Ei tarpeeksi layereita!")
        return
    # Ota Idle-layer referenssiksi
    idle_layer = layers[0]
    idle_img = idle_layer.composite().convert('RGB')
    ref_patch, ref_x, ref_y = extract_reference_patch(idle_img, patch_size)
    print(f"[{os.path.basename(psd_path)}] Referenssialue: x={ref_x}, y={ref_y}, koko={patch_size}x{patch_size}")
    offsets = {}
    for layer in layers[1:]:
        img = layer.composite().convert('RGB')
        best_x, best_y = find_best_patch_xy(img, ref_patch)
        offset_x = best_x - ref_x
        offset_y = best_y - ref_y
        offsets[layer.name] = (offset_x, offset_y)
        print(f"{layer.name}: Paras osuma x={best_x}, y={best_y}, offset_x = {offset_x}, offset_y = {offset_y}")
    # Kirjoita offsetit tiedostoon
    outname = os.path.splitext(os.path.basename(psd_path))[0] + '_offsets.txt'
    with open(outname, 'w', encoding='utf-8') as f:
        for name, (ox, oy) in offsets.items():
            f.write(f"{name}:{ox},{oy}\n")
    print(f"Tallennettu: {outname}")

def main():
    psd_files = [
        'alukset/alus/Corvette_Spritelist.psd',

    ]
    for psd_path in psd_files:
        if os.path.exists(psd_path):
            process_psd_layers(psd_path, patch_size=10)
        else:
            print(f"PSD-tiedostoa ei löydy: {psd_path}")

if __name__ == "__main__":
    main()
