# Builds the 6 weapons (ART_BRIEF §5) as gear overlay sprites, in two sizes:
#   kid (48x48 canvas) and adult (64x64 canvas), each at 16 rotation angles.
# Usage: python tools/build_weapons.py
#        python tools/render.py art/source/gear/weapons_adult.json --out art/out/gear/weapons_adult
#        python tools/render.py art/source/gear/weapons_kid.json --out art/out/gear/weapons_kid
#
# How the game uses them (ART_BRIEF: "a few rotation poses keyed to the grip point"):
#   - Every weapon sprite has its grip at the canvas centre (frames.json "grip").
#   - Frame k is the weapon drawn at k * 22.5 degrees (0 = blade pointing right, 90 = down,
#     screen coordinates), each angle rasterized fresh so the shading and outline stay clean.
#   - Each body frame records the paw's "hand" point and forearm "aim" angle. A weapon held
#     upright in a forward fist points 90 degrees above the forearm, so the game picks
#     frame = round(((aim - 90) mod 360) / 22.5) mod 16 and draws it with its grip on "hand".
#   - Twin knives: the second knife goes on "hand2" (with "aim2"), drawn behind the body.
#   - The rune staff's crystal glows: the game adds its soft glow layer (additive).
# Same house style as Skerbie: straight-edged polygons, flat faceted shading lit from the
# top-left, dark outlines. Weapons are gear, so none of their colours are dye zones.
import json, math, os

PAL = {
    "o": "#0f0d14",                                                   # outline
    "q": "#bfae8c", "r": "#a8945e", "u": "#8b7a4a",                   # bone
    "a": "#7a5636", "b": "#3b2a22",                                   # wood (rough rarity-frame wood, dark wood)
    "w": "#c9cfd6", "i": "#5a5e66", "h": "#33303d",                   # iron: silver edge, iron, charcoal
    "x": "#4a3a5c", "y": "#23212b", "z": "#17151c",                   # obsidian: dusky-purple sheen, black glass
    "P": "#e2b8ff", "Q": "#c77dff", "R": "#9b4dff", "V": "#6a2cc9",   # Mind-magic purple (rune staff crystal)
}
BONE, WOOD, IRON, OBS, RUNE = "qruu", "aaab", "wiih", "xyzz", "PQRV"
LX, LY = -0.6, -0.8  # light from top-left
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def bar(x0, x1, w0, w1):
    # A tapered bar along the weapon's length (x), w wide (across, y).
    return [(x0, -w0 / 2), (x1, -w1 / 2), (x1, w1 / 2), (x0, w0 / 2)]


# Weapons in adult pixels: grip at (0, 0), pointing along +x. Each part: (polygon, ramp).
WEAPONS = {
    "bone_club": [  # common: a big gnawed bone
        ([(-5, -1.8), (-3, -2.6), (-2, 0), (-3, 2.6), (-5, 1.8)], BONE),
        (bar(-3, 14, 3.2, 3.8), BONE),
        ([(12, -2.2), (14, -5), (17.5, -4.6), (19.5, -2.2), (19.5, 2.2), (17.5, 4.6), (14, 5), (12, 2.2)], BONE),
    ],
    "twin_knives": [  # common: one knife (the game draws a second in the far hand)
        (bar(-3.5, 2, 3.2, 3.2), WOOD),
        (bar(2, 3.6, 6, 6), IRON),
        ([(3.6, -2.2), (12.5, -1.6), (16.5, 0.6), (3.6, 2)], IRON),
    ],
    "spear": [  # rare: long ash shaft, leaf-shaped iron head
        (bar(-12, 21, 3.8, 3.8), WOOD),
        (bar(19.5, 21.8, 3, 3), IRON),
        ([(21, 0), (23.5, -2.8), (30, 0), (23.5, 2.8)], IRON),
    ],
    "hooked_blade": [  # rare: a short blade that sweeps out into a hook
        (bar(-3.5, 3, 2.6, 2.6), WOOD),
        (bar(3, 4.2, 4.6, 4.6), IRON),
        ([(4.2, -1.6), (12, -2.2), (16.5, -5.5), (19, -3.5), (15.5, 0.6), (10, 1.8), (4.2, 1.5)], IRON),
    ],
    "rune_staff": [  # epic: dark wood staff, iron prongs cradling a glowing crystal
        (bar(-13, 19, 3.8, 3.6), WOOD),
        ([(18, -1.5), (20, -3.8), (25.5, -3.4), (21.5, -1.2)], IRON),
        ([(18, 1.5), (20, 3.8), (25.5, 3.4), (21.5, 1.2)], IRON),
        ([(19.5, 0), (22.8, -2.4), (28, 0), (22.8, 2.4)], RUNE),
    ],
    "obsidian_greatsword": [  # epic: wide black-glass blade with a dusky sheen
        ([(-6, -1.6), (-4, -2.2), (-4, 2.2), (-6, 1.6)], IRON),
        (bar(-4, 3, 2.8, 2.8), WOOD),
        (bar(3, 4.8, 9.5, 9.5), IRON),
        ([(4.8, -2.8), (25, -2), (30.5, 0), (25, 2), (4.8, 2.8)], OBS),
    ],
}
# canvas, length scale, thickness scale (kid weapons shrink less across, so shafts keep their wood)
SIZES = {"adult": (64, 1.0, 1.0), "kid": (48, 0.7, 0.9)}


def inside(poly, x, y):
    px, py, hit = x + .5, y + .5, False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[i - 1]
        if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


def tone(n):
    lit = n[0] * LX + n[1] * LY
    return 0 if lit > 0.5 else 1 if lit > -0.15 else 2 if lit > -0.55 else 3


def render(parts, angle, size, scale, thick):
    c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    cx = cy = size / 2
    g, layer = {}, {}
    for k, (poly, ramp) in enumerate(parts):
        local = [(x * scale, y * thick) for x, y in poly]
        pts = [(cx + x * c - y * s, cy + x * s + y * c) for x, y in local]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        mx, my = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        hw, hh = max(1, (max(xs) - min(xs)) / 2), max(1, (max(ys) - min(ys)) / 2)
        for y in range(int(min(ys)) - 1, int(max(ys)) + 2):
            for x in range(int(min(xs)) - 1, int(max(xs)) + 2):
                if 0 <= x < size and 0 <= y < size and inside(pts, x, y):
                    g[(x, y)] = ramp[tone(((x + .5 - mx) / hw, (y + .5 - my) / hh))]
                    layer[(x, y)] = k
    # Separate parts with a dark seam, then outline the whole weapon.
    for p, k in list(layer.items()):
        if any(layer.get((p[0] + dx, p[1] + dy), k) < k for dx, dy in N4):
            g[p] = "o"
    filled = set(g)
    for (x, y) in filled:
        if any((x + dx, y + dy) not in filled for dx, dy in N4):
            g[(x, y)] = "o"
    return ["".join(g.get((x, y), ".") for x in range(size)) for y in range(size)]


os.makedirs("art/source/gear", exist_ok=True)
for name, (size, scale, thick) in SIZES.items():
    anims = {w: [render(parts, k * 22.5, size, scale, thick) for k in range(16)] for w, parts in WEAPONS.items()}
    data = {"width": size, "height": size, "fps": 10, "palette": PAL, "dye_zones": {},
            "grip": [size // 2, size // 2], "angle_step": 22.5,
            "attach": {}, "animations": anims}
    json.dump(data, open(f"art/source/gear/weapons_{name}.json", "w"), indent=1)
    print(f"weapons_{name}: {len(anims)} weapons x 16 angles, {size}x{size}")
