
# Uusi: Käytetään HSV-väriavaruutta ja laajempaa sinisen haarukkaa
import os
from PIL import Image
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
    # Sum of squared differences for all pixels
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

def main():
    idle_dir = 'alukset/alus/Corvette/Idle'
    idle_file = '000_Idle_0.png'
    idle_path = os.path.join(idle_dir, idle_file)
    sprite_dir = 'alukset/alus/Corvette/Damage'
    sprite_files = [
        'Damage_1.png', 'Damage_2.png', 'Damage_3.png', 'Damage_4.png',
        'Damage_5.png', 'Damage_6.png', 'Damage_7.png', 'Damage_8.png', 'Damage_9.png'
    ]
    patch_size = 10
    if not os.path.exists(idle_path):
        print(f"Idle-spriteä {idle_file} ei löydy!")
        return
    idle_img = Image.open(idle_path).convert('RGB')
    ref_patch, ref_x, ref_y = extract_reference_patch(idle_img, patch_size)
    print(f"Käytetään referenssialuetta: x={ref_x}, y={ref_y}, koko={patch_size}x{patch_size}")
    offsets = {}
    for fname in sprite_files:
        path = os.path.join(sprite_dir, fname)
        if not os.path.exists(path):
            print(f"{fname}: Ei löydy")
            continue
        img = Image.open(path).convert('RGB')
        best_x, best_y = find_best_patch_xy(img, ref_patch)
        offset_x = best_x - ref_x
        offset_y = best_y - ref_y
        offsets[fname] = (offset_x, offset_y)
        print(f"{fname}: Paras osuma x={best_x}, y={best_y}, offset_x = {offset_x}, offset_y = {offset_y}")
        print(f"# Koodi: offset_x_{fname.replace('.png','')} = {offset_x}, offset_y_{fname.replace('.png','')} = {offset_y}")
    # Kirjoita offsetit tiedostoon
    with open('damage_sprite_offsets.txt', 'w', encoding='utf-8') as f:
        for fname in sprite_files:
            if fname in offsets:
                ox, oy = offsets[fname]
                f.write(f"{fname}:{ox},{oy}\n")


if __name__ == "__main__":
    main()
