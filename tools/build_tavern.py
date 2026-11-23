# Builds the tavern background (ART_BRIEF §8, TAV-BG): The Gnarled Tankard, portrait 225x487.
# Usage: python tools/build_tavern.py
#        python tools/render.py art/source/tavern/tavern_bg.json --out art/out/tavern/tavern_bg --scale 2
#
# A smoky, lantern-lit wooden hall dug into a hill. Top to bottom: the earthen ceiling with
# heavy timber beams and the hanging sign, the gallery (where the upper crowd stands), the
# hanging lanterns, the long bar with its back shelf of bottles and the barrel rack, then the
# open plank floor in the middle where Skerbie fights the beast, inside a faded painted ring,
# and a dark foreground edge (where the front crowd row stands).
# The tavern is always lantern-lit (no time of day), so the warm light is baked in: every
# material has a 5-step ramp and a light pass shifts pixels up the ramp near each lantern,
# Bayer-dithered at the edges. Backgrounds have no hard outlines. Colours are from §3.
# The JSON "spots" say where the game places the NPCs, fighters, crowd rows and breakables.
import json, math, os, random

W, H = 225, 487
OUT = "art/source/tavern"
os.makedirs(OUT, exist_ok=True)
RAMP = {  # darkest -> lit
    "earth": ["#17151c", "#2a2036", "#3a2d4a", "#4a3a5c", "#7a5636"],
    "wood":  ["#17151c", "#3b2a22", "#7a5636", "#a8945e", "#ffd08a"],
    "dwood": ["#17151c", "#23212b", "#3b2a22", "#7a5636", "#a8945e"],
    "stone": ["#17151c", "#2a3448", "#3b4a63", "#4d5e7a", "#5a5e66"],
    "iron":  ["#17151c", "#33303d", "#5a5e66", "#c9cfd6", "#c9cfd6"],
    "root":  ["#17151c", "#23212b", "#3b2a22", "#7a5636", "#8b7a4a"],
    "chalk": ["#2a2036", "#4a3a5c", "#8b7a4a", "#a8945e", "#bfae8c"],
    "bone":  ["#3b2a22", "#8b7a4a", "#a8945e", "#bfae8c", "#ffc8a8"],
}
FIXED = {  # unlit-independent colours (glass, flames)
    "teal": "#2ec4b6", "tealhi": "#8ff0e6", "pink": "#f2a0b0", "amber": "#ffb35c", "moss": "#557a5c",
    "f0": "#ffd08a", "f1": "#ffb35c", "f2": "#ff8a3d", "glass": "#178f86",
}
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
mat = [[("earth", 1)] * W for _ in range(H)]
fixed = {}
rnd = random.Random(11)


def inside(poly, x, y):
    px, py, hit = x + .5, y + .5, False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[i - 1]
        if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


def put(x, y, m, s):
    if 0 <= x < W and 0 <= y < H:
        mat[y][x] = (m, max(0, min(4, s)))
        fixed.pop((x, y), None)


def box(x0, y0, x1, y1, m, s, lit_edge=True):
    # A lit top and left edge, a shadowed bottom and right edge.
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            e = s
            if lit_edge and (y == y0 or x == x0):
                e = s + 1
            if lit_edge and (y == y1 or x == x1):
                e = s - 1
            put(x, y, m, e)


def poly(pts, m, s):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    for y in range(int(min(ys)), int(max(ys)) + 1):
        for x in range(int(min(xs)), int(max(xs)) + 1):
            if inside(pts, x, y):
                put(x, y, m, s(x, y) if callable(s) else s)


def disc(cx, cy, r, m, s):
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            d = math.hypot(x + .5 - cx, y + .5 - cy)
            if d <= r:
                lit = ((x + .5 - cx) * -0.6 + (y + .5 - cy) * -0.8) / r
                put(x, y, m, s + (1 if lit > 0.45 else -1 if lit < -0.5 else 0))


def noise(x, y, scale, seed):
    def h(ix, iy):
        return random.Random(ix * 7919 + iy * 104729 + seed * 31337).random()
    fx, fy = x / scale, y / scale
    ix, iy = int(math.floor(fx)), int(math.floor(fy))
    tx, ty = fx - ix, fy - iy
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    a = h(ix, iy) + (h(ix + 1, iy) - h(ix, iy)) * tx
    b = h(ix, iy + 1) + (h(ix + 1, iy + 1) - h(ix, iy + 1)) * tx
    return a + (b - a) * ty


def root(points, w0, w1):
    pts = []
    for i in range(len(points) - 1):
        (x0, y0), (x1, y1) = points[i], points[i + 1]
        n = max(2, int(math.hypot(x1 - x0, y1 - y0)))
        pts += [(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n) for k in range(n)]
    for k, (cx, cy) in enumerate(pts):
        r = (w0 + (w1 - w0) * k / max(1, len(pts) - 1)) / 2
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                d = math.hypot(x + .5 - cx, y + .5 - cy)
                if d <= r:
                    lit = ((x + .5 - cx) * -0.6 + (y + .5 - cy) * -0.8) / max(r, .5)
                    put(x, y, "root", 3 if lit > 0.5 else 2 if lit > -0.4 else 1)


# ---- key heights
BEAM1, BEAM2 = 30, 96            # ceiling crossbeams
GALLERY = 152                    # gallery floor (upper crowd stands on it)
SHELF1, SHELF2 = 226, 254        # back-bar shelves
BAR_TOP, BAR_BOT = 286, 336      # bar counter
FLOOR = 336                      # back edge of the floor
FIGHT = 424                      # where the fighters' feet are
FRONT = 452                      # dark foreground edge (front crowd row)

# ---- 1. Earth of the hill everywhere, in soft patches, with roots breaking through the ceiling
for y in range(H):
    for x in range(W):
        n = noise(x, y, 14, 1)
        put(x, y, "earth", 2 if n > 0.62 else 1 if n > 0.2 else 0)
for pts, w0, w1 in (([(30, -2), (40, 14), (36, 28)], 6, 2), ([(150, -2), (138, 12), (144, 26)], 7, 2),
                    ([(95, -2), (100, 10), (96, 22)], 4, 1.5), ([(200, 0), (190, 20), (196, 28)], 5, 2)):
    root(pts, w0, w1)

# ---- 2. Back wall: vertical planks between the posts, from the top beam down to the bar
for x in range(16, 210):
    plank = (x - 16) // 7
    seam = (x - 16) % 7 == 0
    for y in range(BEAM1 + 6, BAR_BOT):
        s = 0 if seam else (1 if random.Random(plank).random() < 0.75 else 2)
        if not seam and (x - 16) % 7 == 1:
            s += 1
        put(x, y, "dwood", s)
    if rnd.random() < 0.4:                                     # a knot here and there
        ky = rnd.randint(BEAM2 + 8, BAR_TOP - 10)
        put(x, ky, "dwood", 0)

# ---- 3. The gallery: a dark recess behind a railed balcony (the upper crowd stands in it)
for y in range(BEAM2 + 6, GALLERY):
    for x in range(16, 210):
        put(x, y, "earth", 0 if noise(x, y, 6, 9) < 0.7 else 1)
box(14, GALLERY, 210, GALLERY + 7, "wood", 2)
for x in range(14, 210):
    put(x, GALLERY + 8, "dwood", 0)
box(14, GALLERY - 22, 210, GALLERY - 19, "wood", 2)           # top rail
for x in range(20, 210, 12):                                   # balusters
    box(x, GALLERY - 19, x + 2, GALLERY - 1, "wood", 2)

# ---- 4. Timber frame: posts, crossbeams, braces
for x0 in (6, 209):
    box(x0, 0, x0 + 9, FRONT, "wood", 2)
    for y in range(4, FRONT, 23):                              # grain marks
        put(x0 + 4, y, "wood", 1)
        put(x0 + 5, y + 1, "wood", 1)
box(0, BEAM1, W - 1, BEAM1 + 6, "wood", 2)
box(0, BEAM2, W - 1, BEAM2 + 6, "wood", 2)
for (ax, ay), (bx, by) in (((16, BEAM2 + 6), (40, BEAM2 + 30)), ((208, BEAM2 + 6), (184, BEAM2 + 30)),
                           ((16, BEAM1 + 6), (34, BEAM1 + 24)), ((208, BEAM1 + 6), (190, BEAM1 + 24))):
    for t in range(0, 101):
        x, y = int(ax + (bx - ax) * t / 100), int(ay + (by - ay) * t / 100)
        for d in range(4):
            put(x + (d if ax < 100 else -d), y, "wood", 2 if d else 3)
for x0 in (16, 60, 104, 148, 192):                             # iron straps on the beams
    for y0 in (BEAM1, BEAM2):
        box(x0, y0, x0 + 2, y0 + 6, "iron", 1, lit_edge=False)
        put(x0 + 1, y0 + 3, "iron", 3)

# ---- 5. The sign: a carved board with a gnarled tankard, hung from the top beam
SX0, SX1, SY0, SY1 = 80, 144, 46, 74
for x in (SX0 + 8, SX1 - 8):
    for y in range(BEAM1 + 7, SY0):
        put(x, y, "iron", 2 if y % 2 else 1)
poly([(SX0, SY0 + 2), (SX0 + 3, SY0), (SX1 - 3, SY0), (SX1, SY0 + 2), (SX1, SY1 - 2), (SX1 - 3, SY1),
      (SX0 + 3, SY1), (SX0, SY1 - 2)], "wood", lambda x, y: 3 if y == SY0 or x == SX0 else 1 if y >= SY1 - 1 else 2)
poly([(SX0 + 3, SY0 + 3), (SX1 - 3, SY0 + 3), (SX1 - 3, SY1 - 3), (SX0 + 3, SY1 - 3)], "dwood", 2)
cx = (SX0 + SX1) // 2
box(cx - 9, SY0 + 7, cx + 5, SY1 - 6, "bone", 2)               # the tankard body
box(cx - 10, SY0 + 6, cx + 6, SY0 + 8, "bone", 3)              # rim
for y in range(SY0 + 9, SY1 - 8):                              # handle
    put(cx + 8, y, "bone", 2)
put(cx + 7, SY0 + 9, "bone", 2)
put(cx + 7, SY1 - 9, "bone", 2)
for y in range(SY0 + 9, SY1 - 6, 3):                           # carved hoops and knots: "gnarled"
    for x in range(cx - 9, cx + 6):
        if (x + y) % 5 == 0:
            put(x, y, "bone", 1)
for x in range(cx - 7, cx + 3, 3):                             # foam
    put(x, SY0 + 5, "bone", 4)

# ---- 6. Back-bar shelves with bottles and jars
for sy in (SHELF1, SHELF2):
    box(66, sy, 156, sy + 3, "wood", 2)
    for bx in (70, 150):
        box(bx, sy + 4, bx + 2, sy + 8, "dwood", 2)
    x = 69
    while x < 150:
        kind = rnd.choice(("bottle", "bottle", "jar", "gap"))
        col = rnd.choice(("teal", "pink", "amber", "moss", "glass"))
        if kind == "bottle":
            hgt = rnd.randint(9, 13)
            for y in range(sy - hgt, sy):
                for xx in range(x, x + 4):
                    fixed[(xx, y)] = col
            for y in range(sy - hgt - 3, sy - hgt):
                fixed[(x + 1, y)] = col
                fixed[(x + 2, y)] = col
            fixed[(x + 1, sy - hgt - 4)] = "f0" if col == "amber" else "tealhi" if col in ("teal", "glass") else "pink"
            fixed[(x, sy - hgt + 1)] = "tealhi" if col != "amber" else "f0"   # glint
            x += 6
        elif kind == "jar":
            for y in range(sy - 8, sy):
                for xx in range(x, x + 7):
                    put(xx, y, "chalk", 2 if xx > x else 3)
            box(x, sy - 9, x + 6, sy - 8, "wood", 2, lit_edge=False)
            x += 9
        else:
            x += 5

# ---- 7. The bar counter
box(62, BAR_TOP, 160, BAR_TOP + 5, "wood", 3)                  # worn top, catching the light
for x in range(62, 161):
    put(x, BAR_TOP + 6, "dwood", 0)
for x0 in range(64, 158, 24):                                  # front panels with trim
    box(x0, BAR_TOP + 7, x0 + 22, BAR_BOT - 4, "dwood", 2)
    box(x0 + 3, BAR_TOP + 10, x0 + 19, BAR_BOT - 7, "dwood", 1)
box(62, BAR_BOT - 3, 160, BAR_BOT, "wood", 1)                  # kick rail
for x in range(68, 158, 46):                                   # iron studs
    put(x, BAR_TOP + 2, "iron", 3)

# ---- 8. Barrel rack on the right: barrels lying on their sides, round ends towards us
def barrel(cx, cy, r, tap=False):
    disc(cx, cy, r, "wood", 2)
    for y in range(int(cy - r), int(cy + r) + 1):              # staves
        for x in range(int(cx - r), int(cx + r) + 1):
            if math.hypot(x + .5 - cx, y + .5 - cy) <= r and (x - int(cx)) % 4 == 0:
                put(x, y, "wood", mat[y][x][1] - 1)
    for rr in (r - 0.5, r * 0.55):                             # iron hoops
        for a in range(0, 360, 4):
            x = int(cx + rr * math.cos(math.radians(a)))
            y = int(cy + rr * math.sin(math.radians(a)))
            put(x, y, "iron", 3 if 180 < a < 300 else 2)
    if tap:
        box(int(cx) - 1, int(cy) + 2, int(cx) + 2, int(cy) + 5, "chalk", 3, lit_edge=False)
        put(int(cx), int(cy) + 6, "chalk", 4)


box(162, BAR_BOT - 52, 208, BAR_BOT - 49, "wood", 2)           # rack shelf
for cx, cy, r, tap in ((174, BAR_BOT - 13, 11, True), (197, BAR_BOT - 13, 11, True),
                       (185, BAR_BOT - 64, 11, True), (174, BAR_BOT - 87, 0, False)):
    if r:
        barrel(cx, cy, r, tap)
for x0 in (163, 206):
    box(x0, BAR_BOT - 52, x0 + 2, BAR_BOT, "dwood", 2)

# ---- 9. The plank floor, the faded fight ring, and the dark foreground edge
y = FLOOR
row = 0
while y < H:
    hgt = 5 + (y - FLOOR) // 30                                # planks get taller towards the viewer
    off = rnd.randint(0, 40)
    for yy in range(y, min(H, y + hgt)):
        for x in range(W):
            if x in range(6, 16) or x in range(209, 219):
                if yy < FRONT:
                    continue
            seam = yy == y
            end = (x + off + row * 17) % 53 == 0
            seg = (x + off + row * 17) // 53
            base = 2 if random.Random(row * 31 + seg).random() < 0.7 else 1
            s = 0 if (seam or end) else base + (1 if yy == y + 1 else 0)
            put(x, yy, "dwood", s)
    y += hgt
    row += 1
for x in range(W):
    put(x, FLOOR, "dwood", 0)
    put(x, FLOOR + 1, "dwood", 1)
RX, RY, RW, RH = 112, (FLOOR + FRONT) // 2 + 6, 98, 30         # the painted ring, worn and patchy
for a10 in range(0, 3600, 3):
    a = math.radians(a10 / 10)
    for dr in (0, 0.9):
        x = int(RX + (RW + dr * 1.5) * math.cos(a))
        y = int(RY + (RH + dr) * math.sin(a))
        if noise(x, y, 5, 4) > 0.3 and FLOOR + 2 <= y < FRONT + 8:
            put(x, y, "chalk", 2 if noise(x, y, 3, 5) > 0.5 else 3)
for y in range(FRONT, H):                                      # foreground falls into shadow
    for x in range(W):
        m, s = mat[y][x]
        put(x, y, m, s - (1 + (y - FRONT) // 14))

# ---- 10. Clutter: the hearth, herbs drying under the gallery, wall trophies, tables and stools
HX0, HX1, HTOP = 16, 58, 238                                   # stone hearth on the left wall
for y in range(GALLERY + 9, BAR_BOT + 1):                      # chimney breast, then the wide hearth
    x0, x1 = (24, 50) if y < HTOP else (HX0, HX1)
    course = (y - GALLERY) // 5
    for x in range(x0, x1 + 1):
        joint = (y - GALLERY) % 5 == 0 or (x + (course % 2) * 4) % 8 == 0
        lit = x < x0 + 2 or random.Random(course * 13 + x // 8).random() < 0.3
        put(x, y, "stone", 0 if joint else (2 if lit else 1))
box(HX0 - 2, HTOP - 3, HX1 + 2, HTOP, "wood", 2)                # mantel shelf
for y in range(300, BAR_BOT + 1):                              # the fire mouth: an arched opening
    for x in range(24, 51):
        dx = (x - 37) / 13.5
        if y >= 314 - 14 * math.sqrt(max(0, 1 - dx * dx)):
            put(x, y, "earth", 0)
for k in range(8):                                             # logs
    put(26 + k * 3, BAR_BOT - 1, "wood", 2)
    put(27 + k * 3, BAR_BOT - 2, "wood", 1)
for y in range(314, BAR_BOT - 2):                              # the fire (an animated overlay can sit on "hearth_fire")
    for x in range(27, 48):
        hgt = 10 + 6 * math.sin(x * 0.9) + (3 if x % 5 == 0 else 0)
        d = (BAR_BOT - 2 - y) / hgt
        if d < 1 and abs(x - 37.5) < 11 * (1 - d * 0.6):
            fixed[(x, y)] = "f0" if d < 0.35 and abs(x - 37.5) < 6 else "f1" if d < 0.7 else "f2"
for x, kind in ((20, "candle"), (30, "mug"), (44, "mug"), (55, "candle")):   # things on the mantel
    if kind == "candle":
        box(x, HTOP - 8, x + 1, HTOP - 4, "chalk", 3, lit_edge=False)
        fixed[(x, HTOP - 9)] = "f0"
        fixed[(x + 1, HTOP - 10)] = "f1"
    else:
        box(x, HTOP - 8, x + 4, HTOP - 4, "wood", 2)
        put(x + 5, HTOP - 7, "wood", 1)
        put(x + 5, HTOP - 6, "wood", 1)

# an antlered skull mounted on the chimney breast
SKX, SKY = 37, 200
box(SKX - 6, SKY - 4, SKX + 6, SKY + 9, "dwood", 2)            # the plaque
disc(SKX, SKY + 1, 4.5, "bone", 2)
box(SKX - 2, SKY + 4, SKX + 2, SKY + 8, "bone", 2, lit_edge=False)
put(SKX - 2, SKY + 1, "earth", 0)
put(SKX + 2, SKY + 1, "earth", 0)
for side in (-1, 1):
    pts = [(SKX + side * 3, SKY - 2), (SKX + side * 8, SKY - 8), (SKX + side * 9, SKY - 14), (SKX + side * 12, SKY - 18)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        for t in range(11):
            for w in (0, 1):
                put(int(ax + (bx - ax) * t / 10) + w, int(ay + (by - ay) * t / 10), "bone", 3 - w)
    for (ax, ay) in ((SKX + side * 8, SKY - 8), (SKX + side * 9, SKY - 14)):
        put(int(ax + side * 2), int(ay - 2), "bone", 2)
        put(int(ax + side * 3), int(ay - 3), "bone", 2)

# a round shield with two crossed spears over the barrel rack
SHX, SHY = 186, 206
for side in (-1, 1):
    for t in range(-18, 19):
        put(SHX + t, int(SHY + side * t * 0.8), "wood", 2)
    for k in (18, 19):
        put(SHX + k, int(SHY + side * k * 0.8), "iron", 3)
disc(SHX, SHY, 9, "wood", 2)
for a in range(0, 360, 6):
    put(int(SHX + 8.5 * math.cos(math.radians(a))), int(SHY + 8.5 * math.sin(math.radians(a))), "iron", 2)
for x in range(SHX - 8, SHX + 9, 4):
    for y in range(SHY - 7, SHY + 8):
        if math.hypot(x - SHX, y - SHY) < 8 and abs(x - SHX) > 2:
            put(x, y, "wood", 1)
disc(SHX, SHY, 2.4, "iron", 2)

# herbs and garlic drying from a rod under the gallery
box(62, GALLERY + 9, 160, GALLERY + 10, "dwood", 2, lit_edge=False)
for i, x in enumerate(range(66, 158, 9)):
    put(x, GALLERY + 11, "root", 2)
    if i % 3 == 2:                                             # a string of garlic
        for k in range(3):
            disc(x, GALLERY + 13 + k * 3, 1.5, "bone", 2)
    else:                                                      # an upside-down herb bundle
        ln = 7 + (i * 3) % 4
        for k in range(ln):
            w = 1 + k // 3
            for dx in range(-w, w + 1):
                if (i + k + dx) % 3:
                    fixed[(x + dx, GALLERY + 12 + k)] = "moss"
                else:
                    put(x + dx, GALLERY + 12 + k, "root", 3)
        put(x, GALLERY + 12, "wood", 2)


# tables and stools at the back of the floor, clear of the fight ring
def table(x0, x1, top):
    box(x0, top, x1, top + 3, "wood", 3)
    box(x0 + 1, top + 4, x1 - 1, top + 5, "wood", 1, lit_edge=False)
    cx = (x0 + x1) // 2
    box(cx - 2, top + 6, cx + 2, top + 18, "wood", 2)
    box(cx - 7, top + 18, cx + 7, top + 20, "wood", 2)


def stool(cx, top):
    box(cx - 5, top, cx + 5, top + 2, "wood", 3)
    for lx in (cx - 4, cx + 4):
        for y in range(top + 3, top + 11):
            put(lx + (1 if lx < cx else -1) * ((y - top) // 4), y, "wood", 2)
            put(lx + (1 if lx < cx else -1) * ((y - top) // 4) + 1, y, "wood", 1)


def mug(x, base, foam=True):
    box(x, base - 5, x + 3, base - 1, "wood", 2)
    put(x + 4, base - 4, "wood", 1)
    put(x + 4, base - 3, "wood", 1)
    if foam:
        for xx in range(x, x + 4):
            put(xx, base - 6, "bone", 4)


table(14, 42, FLOOR + 4)
stool(51, FLOOR + 12)
mug(19, FLOOR + 4)
mug(32, FLOOR + 4, foam=False)
table(176, 208, FLOOR + 4)
stool(166, FLOOR + 12)
mug(186, FLOOR + 4)
mug(196, FLOOR + 4)

# ---- 11. Hanging lanterns (chains from the lower beam) and the light they throw
LANTERNS = [(80, 182), (126, 196), (176, 182)]
for lx, ly in LANTERNS:
    for y in range(BEAM2 + 7, ly - 6):
        put(lx, y, "iron", 2 if y % 3 else 1)
    box(lx - 4, ly - 6, lx + 4, ly - 5, "iron", 2, lit_edge=False)
    poly([(lx - 4, ly - 4), (lx + 4, ly - 4), (lx + 3, ly + 5), (lx - 3, ly + 5)], "iron", 1)
    box(lx - 3, ly + 6, lx + 3, ly + 7, "iron", 2, lit_edge=False)
    for y in range(ly - 3, ly + 5):
        for x in range(lx - 2, lx + 3):
            d = abs(x - lx) + abs(y - ly - 1) * 0.7
            fixed[(x, y)] = "f0" if d < 1.5 else "f1" if d < 2.8 else "f2"
LIGHTS = [(lx, ly, 80, 1.5) for lx, ly in LANTERNS] + [(112, 400, 110, 0.8), (100, 250, 50, 0.4),
                                                       (37, 324, 70, 1.8)]   # the hearth fire

# ---- 12. Light pass + smoke haze, then turn materials into colours
pal, inv, rows = {}, {}, []
chars = iter("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")


def code(col):
    if col not in inv:
        inv[col] = next(chars)
        pal[inv[col]] = col
    return inv[col]


for y in range(H):
    line = []
    for x in range(W):
        if (x, y) in fixed:
            line.append(code(FIXED[fixed[(x, y)]]))
            continue
        m, s = mat[y][x]
        light = 0.0
        for lx, ly, rad, k in LIGHTS:
            d = math.hypot((x - lx) * 0.9, (y - ly) * 1.1)
            light += k * max(0.0, 1 - d / rad) ** 1.6
        haze = 0.0
        if y < GALLERY:                                        # pipe smoke hanging under the ceiling
            n = noise(x, y * 2.2, 22, 13)
            haze = max(0.0, n - 0.6) * 1.6 * (1 - y / GALLERY * 0.6)
        v = light + haze
        thr = (BAYER[y % 4][x % 4] + 0.5) / 16
        lift = int(v) + (1 if (v - int(v)) > 0.5 + (thr - 0.5) * 0.4 else 0)
        line.append(code(RAMP[m][max(0, min(4, s + lift))]))
    rows.append("".join(line))

SPOTS = {  # pixel positions the game uses (feet / bottom-centre unless noted)
    "badger": [110, BAR_TOP],          # stands behind the bar; his sprite's bottom is hidden by the counter
    "druid": [196, FIGHT - 4],        # at the ring's edge, right side
    "skerbie": [70, FIGHT],
    "beast": [156, FIGHT],
    "crowd_gallery": [112, GALLERY],  # bottom-centre of the upper crowd row
    "crowd_front": [112, H],          # bottom-centre of the front crowd row
    "chairs": [[30, FRONT - 6], [196, FRONT - 6]],
    "mugs": [[78, BAR_TOP], [134, BAR_TOP], [150, BAR_TOP]],
    "hearth_fire": [37, BAR_BOT - 2],  # bottom-centre of the hearth fire, for an animated flame overlay
    "lanterns": [[lx, ly] for lx, ly in LANTERNS],
}
json.dump({"width": W, "height": H, "fps": 1, "palette": pal, "dye_zones": {}, "attach": {},
           "spots": SPOTS, "animations": {"bg": [rows]}}, open(f"{OUT}/tavern_bg.json", "w"))
print("wrote tavern_bg", len(pal), "colours")
