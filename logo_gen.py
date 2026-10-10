#!/usr/bin/env python3
"""
logo_gen.py - Générateur du logo officiel original "Échiquier Hexagonal 3D"
Génère un logo vectoriel et matriciel haute définition (512x512)
avec export multi-plateformes : .ico (Windows), .png (Linux/macOS/Android).
"""

import os
import math
from PIL import Image, ImageDraw, ImageFilter

def create_hexagonal_logo(size=1024):
    """
    Crée un logo hexagonal 3D haute résolution (1024x1024)
    puis l'échantillonne à 512x512 avec antialiasing Lanczos.
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = size // 2, size // 2 - 20
    radius = int(size * 0.42)
    depth = int(size * 0.16)

    # 1. Ombre portée douce sous le prisme hexagonal
    shadow_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow_img)
    s_cx, s_cy = cx, cy + depth + 40
    s_rx, s_ry = int(radius * 0.95), int(radius * 0.45)
    s_draw.ellipse([s_cx - s_rx, s_cy - s_ry, s_cx + s_rx, s_cy + s_ry], fill=(15, 23, 42, 160))
    shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(32))
    img.paste(shadow_img, (0, 0), shadow_img)

    # 2. Calcul des 6 sommets de la face supérieure hexagonale
    # Angle 30°, 90°, 150°, 210°, 270°, 330° (orientation sommet en haut et en bas)
    top_points = []
    for i in range(6):
        angle_deg = 30 + i * 60
        rad = math.radians(angle_deg)
        # Écrasement vertical (projection isométrique ratio 0.62)
        px = cx + radius * math.cos(rad)
        py = cy + radius * math.sin(rad) * 0.62
        top_points.append((px, py))

    # Sommets de la base inférieure (décalés vers le bas de 'depth')
    bottom_points = [(px, py + depth) for px, py in top_points]

    # 3. Facettes 3D inférieures (côtés du prisme)
    # Face gauche (points 1 -> 2 -> b2 -> b1)
    facet_left = [top_points[1], top_points[2], bottom_points[2], bottom_points[1]]
    draw.polygon(facet_left, fill=(16, 185, 129, 255)) # Émeraude vibrante

    # Face avant-centre (points 0 -> 1 -> b1 -> b0)
    facet_center = [top_points[0], top_points[1], bottom_points[1], bottom_points[0]]
    draw.polygon(facet_center, fill=(5, 150, 105, 255)) # Émeraude sombre

    # Face droite (points 5 -> 0 -> b0 -> b5)
    facet_right = [top_points[5], top_points[0], bottom_points[0], bottom_points[5]]
    draw.polygon(facet_right, fill=(4, 120, 87, 255)) # Émeraude profonde

    # Biseau doré inférieur
    for i in [1, 0, 5]:
        next_i = (i + 1) % 6
        draw.line([bottom_points[i], bottom_points[next_i]], fill=(245, 158, 11, 230), width=6)
        draw.line([top_points[i], bottom_points[i]], fill=(217, 119, 6, 230), width=6)

    # 4. Face supérieure : Échiquier hexagonal isométrique à 19 cases hexagonales
    draw.polygon(top_points, fill=(248, 250, 252, 255)) # Base claire

    # Rendu des cellules de l'échiquier (découpage régulier de la face supérieure)
    # On subdivise en triangles / losanges isométriques pour former un échiquier moderne
    # Alternance de tuiles Blanc Crème (#F1F5F9) et Émeraude (#10B981 / #34D399) et Or (#F59E0B)
    segments = 4
    for row in range(-segments, segments + 1):
        for col in range(-segments, segments + 1):
            if abs(row) + abs(col) > segments + 1:
                continue
            # Position locale
            u = col / float(segments)
            v = row / float(segments)
            # Transformation isométrique vers l'hexagone
            iso_x = cx + (u * 0.866) * radius * 0.88
            iso_y = cy + (v * 0.5 - u * 0.25) * radius * 0.58
            
            # Vérifier si à l'intérieur
            dist_center = math.hypot(iso_x - cx, (iso_y - cy) / 0.62)
            if dist_center < radius * 0.82:
                tile_rad = radius * 0.13
                # Choisir couleur de la tuile
                is_alt = (row + col) % 2 == 0
                if (row == 0 and col == 0):
                    tile_col = (245, 158, 11, 255) # Or central
                    tile_border = (217, 119, 6, 255)
                elif is_alt:
                    tile_col = (16, 185, 129, 240) # Émeraude
                    tile_border = (5, 150, 105, 255)
                else:
                    tile_col = (255, 255, 255, 245) # Blanc pur
                    tile_border = (226, 232, 240, 255)
                
                # Petit losange / hexagone de tuile
                tile_pts = []
                for a in range(6):
                    arad = math.radians(30 + a * 60)
                    tx = iso_x + tile_rad * math.cos(arad)
                    ty = iso_y + tile_rad * math.sin(arad) * 0.62
                    tile_pts.append((tx, ty))
                draw.polygon(tile_pts, fill=tile_col)
                draw.line(tile_pts + [tile_pts[0]], fill=tile_border, width=3)

    # Bordure dorée lumineuse autour du plateau supérieur
    draw.polygon(top_points, outline=(245, 158, 11, 255), width=8)

    # 5. Pièces d'échecs stylisées au centre :
    # A gauche : Cavalier stylisé doré (Knight)
    # A droite : Couronne de Roi émeraude/platine
    # Rendu du Cavalier (Gold Knight)
    kx = cx - int(radius * 0.22)
    ky = cy - int(radius * 0.22)
    knight_pts = [
        (kx - 30, ky + 55),
        (kx + 30, ky + 55),
        (kx + 22, ky + 35),
        (kx + 38, ky + 10),
        (kx + 25, ky - 25),
        (kx + 10, ky - 60),
        (kx - 5, ky - 75),
        (kx - 25, ky - 60),
        (kx - 42, ky - 30),
        (kx - 40, ky - 5),
        (kx - 20, ky + 10),
        (kx - 25, ky + 35),
    ]
    # Ombre de la pièce
    k_shadow = [(px + 10, py + 12) for px, py in knight_pts]
    draw.polygon(k_shadow, fill=(15, 23, 42, 100))
    draw.polygon(knight_pts, fill=(245, 158, 11, 255))
    draw.polygon(knight_pts, outline=(254, 243, 199, 255), width=4)

    # Rendu du Roi stylisé (Emerald/White King Crown)
    rx = cx + int(radius * 0.22)
    ry = cy - int(radius * 0.22)
    king_pts = [
        (rx - 32, ry + 55),
        (rx + 32, ry + 55),
        (rx + 28, ry + 25),
        (rx + 38, ry - 15),
        (rx + 18, ry - 5),
        (rx + 20, ry - 45),
        (rx, ry - 18),
        (rx - 20, ry - 45),
        (rx - 18, ry - 5),
        (rx - 38, ry - 15),
        (rx - 28, ry + 25),
    ]
    r_shadow = [(px + 10, py + 12) for px, py in king_pts]
    draw.polygon(r_shadow, fill=(15, 23, 42, 100))
    draw.polygon(king_pts, fill=(79, 70, 229, 255)) # Indigo royal
    draw.polygon(king_pts, outline=(199, 210, 254, 255), width=4)
    # Croix du roi
    cross_w, cross_h = 8, 22
    draw.line([(rx, ry - 48), (rx, ry - 72)], fill=(245, 158, 11, 255), width=6)
    draw.line([(rx - 12, ry - 60), (rx + 12, ry - 60)], fill=(245, 158, 11, 255), width=6)

    # 6. Éclat lumineux / lueur d'étoile
    star_x = cx + int(radius * 0.48)
    star_y = cy - int(radius * 0.38)
    draw.line([(star_x - 16, star_y), (star_x + 16, star_y)], fill=(255, 255, 255, 220), width=4)
    draw.line([(star_x, star_y - 16), (star_x, star_y + 16)], fill=(255, 255, 255, 220), width=4)

    # Redimensionnement Lanczos 512x512
    final_512 = img.resize((512, 512), Image.Resampling.LANCZOS)
    return final_512

def generate_all_icons(output_dir="assets"):
    os.makedirs(output_dir, exist_ok=True)
    
    print("🎨 Génération du logo original 'Échiquier Hexagonal 3D' (512x512)...")
    logo_512 = create_hexagonal_logo(size=1024)
    
    logo_path = os.path.join(output_dir, "logo.png")
    logo_512.save(logo_path, "PNG")
    print(f"✓ Enregistré : {logo_path}")

    # assets/icon.png (256x256 standard)
    icon_256 = logo_512.resize((256, 256), Image.Resampling.LANCZOS)
    icon_path = os.path.join(output_dir, "icon.png")
    icon_256.save(icon_path, "PNG")
    print(f"✓ Enregistré : {icon_path}")

    # assets/icon.ico multi-tailles Windows (16, 32, 48, 64, 128, 256)
    ico_path = os.path.join(output_dir, "icon.ico")
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    logo_512.save(ico_path, format="ICO", sizes=icon_sizes)
    print(f"✓ Enregistré : {ico_path} (Tailles: {icon_sizes})")

    # Copie racine icon.png pour compatibilité
    logo_512.save("icon.png", "PNG")
    print("✓ Enregistré : icon.png (racine)")

if __name__ == "__main__":
    generate_all_icons()
