# Builds the home den backgrounds (ART_BRIEF §6), portrait 225x487, in neutral lighting
# (the time-of-day tint and lantern glow are separate overlays; the sky is a separate layer
# that shows through the transparent area above the treeline).
# Usage: python tools/build_den.py burrow   (look test; hideout and lair come later)
#        python tools/render.py art/source/home/den_burrow.json --out art/out/home/den_burrow --scale 2
#
# Layout (ART_BRIEF §6): top ~30% surface (forest floor, the huge trunk rising out of frame,
# the root door, a garden patch, room for the merchant cart and the overflow pile), middle
# ~50% the den hollowed out under the roots, bottom ~20% the deep roots and stone where the
# Delve crack opens later (its own sprite). Backgrounds have soft or no outlines, so the
# characters pop. Light comes from the top-left. All colours are from the §3 world palette.
import json, math, os, random, sys

TIER = sys.argv[1] if len(sys.argv) > 1 else "burrow"
assert TIER == "burrow", "only the Burrow exists so far"
W, H = 225, 487
GROUND, DEN_TOP, DEN_FLOOR, DEEP = 136, 168, 372, 392   # key heights

PAL = {
    # far forest (slate) and near treeline
    "S": "#4d5e7a", "T": "#3b4a63", "U": "#2a3448",
    # moss and grass on the forest floor
    "G": "#557a5c", "H": "#3e5a46", "I": "#2c4234",
    # soil: dusky purple earth and charcoal
    "p": "#4a3a5c", "q": "#3a2d4a", "r": "#2a2036",
    "c": "#33303d", "d": "#23212b", "e": "#17151c",
    # bark and roots: dark wood with a warm lit edge
    "R": "#3b2a22", "W": "#7a5636", "B": "#8b7a4a",
    # teal shadow for cool depth in the deep roots
    "t": "#1f3d44", "u": "#2c5560",
    # candle: wax, flame
    "y": "#ffc8a8", "Y": "#ffd08a", "Z": "#ffb35c", "O": "#ff8a3d",
}
grid = [["." for _ in range(W)] for _ in range(H)]


def setp(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        grid[y][x] = c


def getp(x, y):
    return grid[y][x] if 0 <= x < W and 0 <= y < H else None


def inside(poly, x, y):
    px, py, hit = x + .5, y + .5, False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[i - 1]
        if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


def fill(poly, colour):
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    for y in range(max(0, int(min(ys))), min(H, int(max(ys)) + 1)):
        for x in range(max(0, int(min(xs))), min(W, int(max(xs)) + 1)):
            if inside(poly, x, y):
                setp(x, y, colour(x, y) if callable(colour) else colour)


def noise(x, y, scale, seed):
    # Smooth value noise in [0, 1): clustered patches instead of salt-and-pepper speckle.
    def h(ix, iy):
        return random.Random(ix * 7919 + iy * 104729 + seed * 31337).random()
    fx, fy = x / scale, y / scale
    ix, iy = int(math.floor(fx)), int(math.floor(fy))
    tx, ty = fx - ix, fy - iy
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    a, b = h(ix, iy) + (h(ix + 1, iy) - h(ix, iy)) * tx, h(ix, iy + 1) + (h(ix + 1, iy + 1) - h(ix, iy + 1)) * tx
    return a + (b - a) * ty


def root(points, w0, w1):
    # A thick, tapering root along a polyline: dark core, warm lit top-left edge, deep shadow below.
    pts = []
    for i in range(len(points) - 1):
        (x0, y0), (x1, y1) = points[i], points[i + 1]
        n = max(2, int(math.hypot(x1 - x0, y1 - y0)))
        pts += [(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n) for k in range(n)]
    total = len(pts)
    mask = {}
    for k, (cx, cy) in enumerate(pts):
        r = (w0 + (w1 - w0) * k / max(1, total - 1)) / 2
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                d = math.hypot(x + .5 - cx, y + .5 - cy)
                if d <= r:
                    lit = ((x + .5 - cx) * -0.6 + (y + .5 - cy) * -0.8) / max(r, 0.5)
                    mask[(x, y)] = max(mask.get((x, y), -9), lit)
    for (x, y), lit in mask.items():
        setp(x, y, "W" if lit > 0.55 else "R" if lit > -0.45 else "e")


# ---- 1. Surface: far forest silhouette, near treeline (the sky shows through above them) ----
rnd = random.Random(7)
# Two rows of conifer silhouettes: a far, darker row and a nearer, lighter one, each tree a
# tall pointed triangle with a stepped (tiered) edge, lit a touch on its left side.
for layer, (hmin, hmax, wmin, wmax, base, lit, body) in enumerate(((48, 78, 10, 16, GROUND, "U", "U"),
                                                                   (34, 60, 12, 20, GROUND, "S", "T"))):
    x = rnd.randint(-8, 0)
    while x < W + 8:
        hgt, half = rnd.randint(hmin, hmax), rnd.randint(wmin, wmax) / 2
        top = base - hgt
        for y in range(int(top), base):
            t = (y - top) / hgt
            tier = 1.6 * ((y - top) % 9) / 9                        # stepped branch tiers
            reach = half * t + tier * t
            for xx in range(int(x - reach), int(x + reach) + 1):
                setp(xx, y, lit if (layer and xx < x - reach * 0.4 and (y // 3) % 2 == 0) else body)
        x += rnd.randint(int(wmin * 0.7), int(wmax * 0.9))

# ---- 2. Soil everywhere below the ground line, with soft strata ----
for y in range(GROUND, H):
    for x in range(W):
        # Mostly one calm earth tone; broad soft patches (large-scale noise) and faint strata.
        n = noise(x, y, 18, 3) + 0.15 * noise(x, y, 5, 4)
        strata = (y + int(6 * noise(x, 0, 30, 14))) % 23 == 0
        if y >= DEEP:  # deep roots and stone: colder, darker, with only a hint of teal
            c = "t" if n > 1.05 else "d" if n > 0.5 else "e"
        else:
            c = "r" if strata or n < 0.35 else "p" if n > 1.0 else "q"
        setp(x, y, c)

# ---- 3. Forest floor: grass and moss along the top of the soil, with tufts ----
for x in range(W):
    lip = GROUND + int(2 * noise(x, 0, 6, 5))
    for y in range(GROUND - 3, lip + 4):
        if y < GROUND:
            if (x * 7 + y) % 5 == 0 and noise(x, y, 3, 6) > 0.45:  # grass tufts
                setp(x, y, "H")
        else:
            setp(x, y, "G" if y < lip + 1 else "H" if y < lip + 3 else "I")

# ---- 4. The huge trunk rising out of frame, its root flare spreading into the ground ----
trunk = [(84, 0), (146, 0), (150, 60), (154, 98), (168, 118), (186, 134), (198, 140),
         (150, 140), (140, 132), (88, 132), (76, 140), (34, 140), (50, 132), (68, 116), (78, 96), (80, 60)]


def bark(x, y):
    # Dark bark with long vertical grain; a warm edge only on the lit left side.
    streak = noise(x * 3, y * 0.25, 4, 8)
    edge = (x - 84) / 62
    if streak < 0.2:
        return "e"
    if edge < 0.12 and streak > 0.62:
        return "B"
    if edge < 0.35 and streak > 0.6:
        return "W"
    return "R" if edge < 0.8 or streak > 0.45 else "e"


fill(trunk, bark)
# The root door: a dark arch in the trunk's base, framed by a lip of root.
door = [(104, 134), (104, 116), (108, 108), (115, 104), (122, 108), (126, 116), (126, 134)]
fill(door, lambda x, y: "e" if y > 110 or noise(x, y, 2, 9) > 0.3 else "d")
root([(100, 135), (101, 116), (106, 106), (115, 101), (124, 106), (129, 116), (130, 135)], 4, 4)

# ---- 5. The den: a hollow under the roots, connected to the door by a shaft ----
den = [(16, 372), (12, 330), (16, 268), (30, 214), (58, 184), (92, 172), (134, 170), (170, 178),
       (196, 200), (210, 244), (214, 300), (211, 346), (206, 372)]
shaft = [(106, 134), (124, 134), (128, 176), (102, 176)]
hollow = set()
for poly in (den, shaft):
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    for y in range(int(min(ys)), int(max(ys)) + 1):
        for x in range(int(min(xs)), int(max(xs)) + 1):
            if inside(poly, x, y):
                hollow.add((x, y))


def rim(x, y, d):
    return any((x + dx, y + dy) not in hollow for dx in range(-d, d + 1) for dy in range(-d, d + 1))


for (x, y) in hollow:
    n = noise(x, y, 22, 12) + 0.12 * noise(x, y, 6, 13)
    if y >= DEN_FLOOR - 6:                      # packed dirt floor, lighter on top
        c = "q" if y < DEN_FLOOR - 3 else "r"
    elif rim(x, y, 2):                          # dark edge where the walls curve away
        c = "e"
    elif rim(x, y, 5):
        c = "d"
    else:                                       # the back wall: smooth dark earth, rare soft patches
        c = "c" if n > 1.04 else "q" if n < 0.14 else "d"
    setp(x, y, c)
for x in range(W):                              # floor edge line, where it meets the back wall
    if (x, DEN_FLOOR - 7) in hollow and (x, DEN_FLOOR - 6) in hollow:
        setp(x, DEN_FLOOR - 6, "p")

# ---- 6. Bare roots: through the soil, across the den ceiling and down the walls ----
ROOTS = [
    ([(88, 138), (70, 150), (44, 166), (22, 196), (10, 236)], 8, 3),
    ([(150, 138), (172, 152), (196, 172), (214, 206)], 8, 3),
    ([(110, 140), (98, 160), (84, 176), (60, 186), (40, 200)], 5, 2),
    ([(132, 140), (148, 162), (168, 182), (184, 206), (188, 232)], 6, 2),
    ([(62, 182), (66, 196), (62, 214)], 3, 1.2),      # dangling root tips in the den
    ([(150, 176), (146, 192), (150, 206)], 3, 1.2),
    ([(112, 172), (110, 186)], 2.4, 1),
    ([(4, 300), (20, 318), (14, 352), (24, 380), (10, 420)], 6, 3),
    ([(221, 290), (208, 330), (216, 368), (204, 410)], 6, 3),
    ([(40, 392), (70, 410), (108, 418), (150, 412), (186, 398)], 7, 4),   # deep roots under the floor
    ([(16, 440), (48, 452), (60, 478), (90, 486)], 6, 3),
    ([(200, 440), (176, 462), (150, 470), (128, 486)], 6, 3),
]
for pts, w0, w1 in ROOTS:
    root(pts, w0, w1)
# Root rungs down the shaft, so he can climb up to the door.
for y in (146, 156, 166):
    root([(104, y), (126, y + 1)], 2.6, 2.6)

# ---- 7. Stones in the deep roots ----
srnd = random.Random(21)
for _ in range(16):
    cx, cy, r = srnd.randint(8, W - 8), srnd.randint(DEEP + 6, H - 6), srnd.uniform(3, 7)
    for y in range(int(cy - r), int(cy + r) + 1):
        for x in range(int(cx - r * 1.4), int(cx + r * 1.4) + 1):
            d = math.hypot((x + .5 - cx) / 1.4, y + .5 - cy)
            if d <= r and getp(x, y) not in ("R", "W", "e"):
                lit = ((x + .5 - cx) * -0.6 + (y + .5 - cy) * -0.8) / r
                setp(x, y, "S" if lit > 0.5 else "T" if lit > -0.3 else "U")

# ---- 8. One candle on a dirt ledge in the left wall (the Burrow's only light) ----
fill([(26, 300), (50, 300), (48, 305), (28, 305)], "p")          # ledge
fill([(36, 290), (40, 290), (40, 300), (36, 300)], "y")          # wax
for (x, y), c in {(38, 288): "Z", (38, 287): "Y", (37, 289): "O", (38, 289): "Y", (39, 289): "O",
                  (38, 286): "Y", (38, 285): "Z"}.items():
    setp(x, y, c)

# Where the buildables and the crack go (ART_BRIEF §6 / BUILD_SPEC §7), for the game to read.
SPOTS = {
    "door": [115, 120], "garden": [190, 132], "merchant_cart": [30, 132], "overflow_pile": [148, 134],
    "bed": [44, 372], "pantry": [70, 300], "workbench": [180, 372], "chest": [140, 372],
    "walls_traps": [115, 176], "training": [96, 372], "hearth": [112, 340], "decor": [38, 300],
    "chalkboard": [196, 300], "blueprint": [166, 240], "radio": [150, 300], "crack": [112, 428],
}
os.makedirs("art/source/home", exist_ok=True)
json.dump({"width": W, "height": H, "fps": 1, "palette": PAL, "dye_zones": {}, "attach": {},
           "spots": SPOTS, "animations": {TIER: [["".join(r) for r in grid]]}},
          open(f"art/source/home/den_{TIER}.json", "w"))
print(f"den_{TIER}: {W}x{H}")
