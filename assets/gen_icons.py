"""
Generate 5 icon option previews + ICO files for PoELens.
Run: python assets/gen_icons.py
"""

import math
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SIZE = 256
OUT = "assets"

# Shared palette
BG      = (13,  13,  26)
GOLD    = (226, 185, 111)
GOLD2   = (200, 155,  75)
TEAL    = ( 74, 232, 200)
SILVER  = (180, 180, 210)
PURPLE  = (154,  74, 232)
BLUE    = ( 74, 138, 232)
DIM     = (58,  58,  90)


def save(img: Image.Image, name: str):
    path_png = f"{OUT}/{name}.png"
    img.save(path_png)
    # Also save as .ico with multiple sizes
    ico_sizes = [(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)]
    ico_imgs = [img.resize(s, Image.LANCZOS) for s in ico_sizes]
    ico_imgs[0].save(f"{OUT}/{name}.ico", format="ICO",
                     sizes=ico_sizes, append_images=ico_imgs[1:])
    print(f"  {name}.png + .ico")


def glow(draw, cx, cy, r, color, steps=6):
    """Paint a radial glow by drawing concentric circles with fading alpha."""
    for i in range(steps, 0, -1):
        alpha = int(180 * (i / steps) ** 2)
        rr = r + (steps - i) * 4
        draw.ellipse([cx-rr, cy-rr, cx+rr, cy+rr],
                     fill=(*color, alpha))


# ─────────────────────────────────────────────────────────────────────────────
# Option 1 — Passive Tree cluster
# Gold nodes connected by lines on dark background; looks like the actual tree
# ─────────────────────────────────────────────────────────────────────────────

def make_tree():
    img = Image.new("RGBA", (SIZE, SIZE), BG)
    gfx = ImageDraw.Draw(img)

    cx, cy = SIZE//2, SIZE//2

    # Define nodes as (angle_deg, radius, type) — type: 0=normal, 1=notable, 2=keystone
    nodes = [
        # center keystone
        (0, 0, 2),
        # inner ring — notables
        (0,   60, 1), (60,  60, 1), (120, 60, 1),
        (180, 60, 1), (240, 60, 1), (300, 60, 1),
        # outer ring — normals
        (30,  105, 0), (90,  105, 0), (150, 105, 0),
        (210, 105, 0), (270, 105, 0), (330, 105, 0),
        # second notable ring (partial)
        (15,  105, 1), (75,  105, 1), (195, 105, 1),
    ]

    def pos(ang, rad):
        a = math.radians(ang - 90)
        return (cx + rad * math.cos(a), cy + rad * math.sin(a))

    # Draw edges
    center = pos(0, 0)
    for ang, rad, _ in nodes[1:7]:
        p = pos(ang, rad)
        gfx.line([center, p], fill=(*DIM, 200), width=2)
    for i, (ang, rad, _) in enumerate(nodes[1:7]):
        p = pos(ang, rad)
        # connect to 2 outer nodes
        for ang2, rad2, _ in nodes[7:]:
            p2 = pos(ang2, rad2)
            dist = math.hypot(p[0]-p2[0], p[1]-p2[1])
            if dist < 70:
                gfx.line([p, p2], fill=(*DIM, 160), width=1)

    # Draw nodes
    for ang, rad, ntype in nodes:
        x, y = pos(ang, rad)
        if ntype == 2:   # keystone
            r, col = 18, GOLD
        elif ntype == 1: # notable
            r, col = 10, SILVER
        else:            # normal
            r, col = 5,  DIM
        glow(gfx, x, y, r, col[:3], steps=4)
        gfx.ellipse([x-r, y-r, x+r, y+r], fill=BG, outline=col, width=2)

    img = img.filter(ImageFilter.GaussianBlur(0.4))
    save(img, "icon_1_tree")


# ─────────────────────────────────────────────────────────────────────────────
# Option 2 — Skill Gem  (hexagon with inner glow, gem facets)
# ─────────────────────────────────────────────────────────────────────────────

def make_gem():
    img = Image.new("RGBA", (SIZE, SIZE), BG)
    gfx = ImageDraw.Draw(img, "RGBA")
    cx, cy = SIZE//2, SIZE//2

    def hex_pts(cx, cy, r, offset=0):
        return [
            (cx + r * math.cos(math.radians(60*i + offset)),
             cy + r * math.sin(math.radians(60*i + offset)))
            for i in range(6)
        ]

    # Outer glow
    for step in range(8, 0, -1):
        alpha = int(120 * (step/8)**2)
        pts = hex_pts(cx, cy, 85 + step*3, offset=0)
        gfx.polygon(pts, fill=(*TEAL, alpha))

    # Outer hex
    gfx.polygon(hex_pts(cx, cy, 88), fill=(20, 30, 50), outline=TEAL, width=3)

    # Facet lines from center
    for ang in range(0, 360, 60):
        tip = (cx + 85 * math.cos(math.radians(ang)),
               cy + 85 * math.sin(math.radians(ang)))
        gfx.line([(cx, cy), tip], fill=(*TEAL, 80), width=1)

    # Inner hex
    gfx.polygon(hex_pts(cx, cy, 54, offset=30), fill=(30, 60, 70), outline=(*TEAL, 200), width=2)

    # Core glow
    glow(gfx, cx, cy, 22, TEAL, steps=5)
    gfx.ellipse([cx-22, cy-22, cx+22, cy+22], fill=TEAL, outline=(255,255,255,180), width=2)

    # Letter H in center
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 26)
    except Exception:
        font = ImageFont.load_default()
    bb = gfx.textbbox((0,0), "H", font=font)
    tw, th = bb[2]-bb[0], bb[3]-bb[1]
    gfx.text((cx - tw//2, cy - th//2 - 2), "H", font=font, fill=BG)

    save(img, "icon_2_gem")


# ─────────────────────────────────────────────────────────────────────────────
# Option 3 — HUD Eye  (targeting reticle with golden iris, overlay vibe)
# ─────────────────────────────────────────────────────────────────────────────

def make_eye():
    img = Image.new("RGBA", (SIZE, SIZE), BG)
    gfx = ImageDraw.Draw(img, "RGBA")
    cx, cy = SIZE//2, SIZE//2

    # Outer ring (reticle)
    gfx.ellipse([cx-100, cy-100, cx+100, cy+100], outline=(*GOLD, 100), width=2)
    # Tick marks at 12/3/6/9
    for ang in [0, 90, 180, 270]:
        a = math.radians(ang)
        x1 = cx + 95 * math.cos(a); y1 = cy + 95 * math.sin(a)
        x2 = cx + 108 * math.cos(a); y2 = cy + 108 * math.sin(a)
        gfx.line([(x1,y1),(x2,y2)], fill=GOLD, width=3)

    # Eye shape (almond)
    eye_w, eye_h = 130, 60
    # top arc
    gfx.arc([cx-eye_w//2, cy-eye_h, cx+eye_w//2, cy+eye_h], start=200, end=340, fill=GOLD, width=3)
    # bottom arc
    gfx.arc([cx-eye_w//2, cy-eye_h, cx+eye_w//2, cy+eye_h], start=20, end=160, fill=GOLD, width=3)

    # Iris
    glow(gfx, cx, cy, 30, GOLD[:3], steps=5)
    gfx.ellipse([cx-32, cy-32, cx+32, cy+32], fill=(40, 30, 10), outline=GOLD, width=3)

    # Pupil
    gfx.ellipse([cx-14, cy-14, cx+14, cy+14], fill=BG, outline=(*GOLD, 180), width=1)

    # Corner reticle marks
    for ang in [45, 135, 225, 315]:
        a = math.radians(ang)
        x1 = cx + 72 * math.cos(a); y1 = cy + 72 * math.sin(a)
        x2 = cx + 85 * math.cos(a); y2 = cy + 85 * math.sin(a)
        gfx.line([(x1,y1),(x2,y2)], fill=(*GOLD, 150), width=2)

    save(img, "icon_3_eye")


# ─────────────────────────────────────────────────────────────────────────────
# Option 4 — Exalted Orb style  (glowing orb with rune circle)
# ─────────────────────────────────────────────────────────────────────────────

def make_orb():
    img = Image.new("RGBA", (SIZE, SIZE), BG)
    gfx = ImageDraw.Draw(img, "RGBA")
    cx, cy = SIZE//2, SIZE//2

    # Deep glow behind orb
    for step in range(10, 0, -1):
        alpha = int(60 * (step/10)**1.5)
        r = 75 + step * 5
        gfx.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(*GOLD, alpha))

    # Orb body gradient (fake it with concentric circles)
    for r in range(72, 0, -1):
        t = r / 72
        col = (
            int(GOLD[0]*t + 60*(1-t)),
            int(GOLD[1]*t + 40*(1-t)),
            int(GOLD[2]*t + 10*(1-t)),
        )
        gfx.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(*col, 255))

    # Orb highlight
    gfx.ellipse([cx-35, cy-45, cx+5, cy-15], fill=(255,245,200,120))

    # Rune circle around orb
    rune_r = 95
    gfx.ellipse([cx-rune_r, cy-rune_r, cx+rune_r, cy+rune_r],
                outline=(*GOLD, 120), width=1)
    # Rune tick marks (12 positions)
    for i in range(12):
        ang = math.radians(i * 30)
        inner = 90; outer = 100 if i % 3 == 0 else 95
        gfx.line([
            (cx + inner*math.cos(ang), cy + inner*math.sin(ang)),
            (cx + outer*math.cos(ang), cy + outer*math.sin(ang)),
        ], fill=(*GOLD, 180 if i % 3 == 0 else 100), width=2 if i%3==0 else 1)

    save(img, "icon_4_orb")


# ─────────────────────────────────────────────────────────────────────────────
# Option 5 — Shield crest  (heraldic shield with "EH" monogram, PoE crest feel)
# ─────────────────────────────────────────────────────────────────────────────

def make_crest():
    img = Image.new("RGBA", (SIZE, SIZE), BG)
    gfx = ImageDraw.Draw(img, "RGBA")
    cx, cy = SIZE//2, SIZE//2 - 8

    # Shield outline (pointed bottom)
    shield = [
        (cx-85, cy-90), (cx+85, cy-90),
        (cx+85, cy+20), (cx,    cy+100),
        (cx-85, cy+20),
    ]
    # Glow behind shield
    for step in range(6, 0, -1):
        expanded = [(x + (1 if x>cx else -1)*step*2,
                     y + (1 if y>cy else -1)*step*2) for x,y in shield]
        gfx.polygon(expanded, fill=(*GOLD, 20))

    gfx.polygon(shield, fill=(20, 18, 35))
    gfx.polygon(shield, outline=GOLD, width=3)

    # Inner shield border
    inner = [(x + (1 if x>cx else -1)*10,
              y + (1 if y>cy else -1)*10) for x,y in shield]
    gfx.polygon(inner, outline=(*GOLD, 100), width=1)

    # Horizontal divider
    gfx.line([(cx-75, cy-20), (cx+75, cy-20)], fill=(*GOLD, 160), width=2)

    # "EH" monogram
    try:
        font_big = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 58)
        font_sub = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 20)
    except Exception:
        font_big = ImageFont.load_default()
        font_sub = font_big

    bb = gfx.textbbox((0,0), "EH", font=font_big)
    tw = bb[2]-bb[0]; th = bb[3]-bb[1]
    gfx.text((cx - tw//2, cy - th//2 - 18), "EH", font=font_big, fill=GOLD)

    # Subtitle
    bb2 = gfx.textbbox((0,0), "EXILE HUD", font=font_sub)
    tw2 = bb2[2]-bb2[0]
    gfx.text((cx - tw2//2, cy + 32), "EXILE HUD", font=font_sub, fill=(*GOLD, 180))

    save(img, "icon_5_crest")


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import os; os.makedirs("assets", exist_ok=True)
    print("Generating icons...")
    make_tree()
    make_gem()
    make_eye()
    make_orb()
    make_crest()
    print("Done. Check assets/ folder for previews.")
