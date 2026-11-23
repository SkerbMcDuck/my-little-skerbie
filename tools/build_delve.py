# Builds the Cave Delve backdrops (ART_BRIEF §11): portrait 225x487 fight chambers, side view,
# Skerbie on the left and enemies on the right; and the descending-stairs transition [6].
# Usage: python tools/build_delve.py [roots|crystal|ruins|deep|stairs ...]
#        python tools/render.py art/source/delve/<zone>_<room>_bg.json --out art/out/delve/<zone>_<room>_bg --scale 2
#
# Per zone, 4 rooms: fight_a, fight_b, treasure (a glowing chest on a pedestal, scattered coins;
# the chest is the Jungle Run chest sprite, placed on "chest_spot") and boss (a bigger, more dramatic
# vault). Layout for every room: the cave ceiling at the top, the chamber wall behind the fight, the
# fight floor at y 330 (spots "skerbie", "enemies"), and a calm dark foreground below for the move and
# item buttons. Same painter as the game scenes (tools/build_scenes.py): 5-step ramps lit by a
# dithered light pass, no hard outlines, colours from §3.
import json, math, os, random, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_scenes as bs  # noqa: E402
from build_scenes import Scene, noise, W, H  # noqa: E402

bs.OUT = "art/source/delve"
os.makedirs(bs.OUT, exist_ok=True)
bs.RAMP.update({
    "cave":   ["#17151c", "#23212b", "#2a2036", "#3a2d4a", "#4a3a5c"],
    "cavef":  ["#17151c", "#23212b", "#2a2036", "#3a2d4a", "#7a5636"],      # floor, warmer when lit
    "root":   ["#17151c", "#23212b", "#3b2a22", "#7a5636", "#8b7a4a"],
    "fungt":  ["#1f3d44", "#178f86", "#2ec4b6", "#8ff0e6", "#8ff0e6"],      # teal glowing fungi
    "fungp":  ["#2a2036", "#4a3a5c", "#f2a0b0", "#ffc8a8", "#ffc8a8"],      # pink glowing fungi
    "water":  ["#17151c", "#1f3d44", "#178f86", "#2ec4b6", "#8ff0e6"],
    "goldc":  ["#3b2a22", "#a8643a", "#f2c14e", "#ffe08a", "#ffe08a"],
    "heart":  ["#2a2036", "#4a3a5c", "#ff8a3d", "#ffb35c", "#ffd08a"],      # the boss root's ember heart
    "cstone": ["#17151c", "#23212b", "#2a3448", "#3b4a63", "#4d5e7a"],      # crystal caverns rock
    "cfloor": ["#17151c", "#23212b", "#2a3448", "#3b4a63", "#4d5e7a"],
    "crys":   ["#1f3d44", "#178f86", "#2ec4b6", "#8ff0e6", "#f2f9ff"],      # glowing crystal
    "crysd":  ["#17151c", "#1f3d44", "#178f86", "#2ec4b6", "#8ff0e6"],
    "mason":  ["#17151c", "#23212b", "#2a2036", "#3a2d4a", "#4a3a5c"],      # sunken ruins masonry
    "mfloor": ["#17151c", "#23212b", "#2a3448", "#3b4a63", "#4d5e7a"],
    "statue": ["#17151c", "#2a3448", "#3b4a63", "#4d5e7a", "#8a8494"],
    "glyph":  ["#2a2036", "#4a3a5c", "#6a2cc9", "#9b4dff", "#c77dff"],      # faint purple rune-light
    "pool":   ["#17151c", "#1f3d44", "#2c5560", "#178f86", "#2ec4b6"],
    "black":  ["#17151c", "#17151c", "#23212b", "#33303d", "#5a5e66"],      # hollow deep obsidian
    "bfloor": ["#17151c", "#17151c", "#23212b", "#33303d", "#4a3a5c"],
    "smoke":  ["#17151c", "#23212b", "#33303d", "#4a3a5c", "#5a5e66"],
    "sick":   ["#17151c", "#2c4234", "#557a5c", "#c8e04a", "#e4f27a"],      # the Hollow's sickly light
    "rag":    ["#17151c", "#2a2036", "#3a2d4a", "#4a3a5c", "#4a3a5c"],
    "chain":  ["#17151c", "#23212b", "#33303d", "#5a5e66", "#c9cfd6"],
})
bs.FIXED.update({"smoke1": "#23212b", "smoke2": "#33303d", "crys0": "#f2f9ff", "crys1": "#8ff0e6", "glyph0": "#c77dff", "glyph1": "#9b4dff",
                 "sick0": "#e4f27a", "sick1": "#c8e04a", "drop": "#8ff0e6", "drop2": "#2ec4b6", "coin": "#f2c14e", "coinhi": "#ffe08a",
                 "fung0": "#8ff0e6", "fungp0": "#ffc8a8", "ember": "#ffb35c", "ember0": "#ffd08a"})
FLOOR = 330          # fighters' feet
FRONT = 372


def curve(pts, wobble=0.0, seed=0):
    # A smooth Catmull-Rom curve through the points, with an optional gentle wobble: organic roots.
    out = []
    P = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        n = max(4, int(math.hypot(p2[0] - p1[0], p2[1] - p1[1]) / 3))
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            x = 0.5 * (2 * p1[0] + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * (2 * p1[1] + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x + wobble * math.sin(len(out) * 0.35 + seed), y + wobble * math.cos(len(out) * 0.29 + seed)))
    out.append(pts[-1])
    return out


def root(sc, pts, w0, w1, seed=0):
    sc.branch(curve(pts, 1.2, seed), w0, w1, "root", 2)          # where the calm foreground begins (the move / item buttons sit over it)


def cave_shell(sc, seed, vault=False, wall="cave", floor="cavef", calm=False):
    # Solid rock everywhere, a chamber hollowed out of it: an arched back wall, a floor, a foreground lip.
    top = 46 if vault else 70
    for y in range(H):
        for x in range(W):
            n = noise(x, y, 9, seed)
            sc.put(x, y, wall, 1 if n > (0.75 if calm else 0.6) else 0)
    for y in range(top, FLOOR + 1):                                            # the hollow: a lighter back wall
        for x in range(W):
            edge = 18 * (1 - ((y - top) / (FLOOR - top))) ** 0.5 if not vault else 8 * (1 - ((y - top) / (FLOOR - top)))
            arch = top + 30 * (abs(x - 112) / 112) ** 2.2
            if y > arch and edge < x < W - edge:
                n = noise(x, y, 7, seed + 1)
                if calm:
                    sc.put(x, y, wall, 2 if (n > 0.8 or (y > top + 60 and noise(x, y, 3, seed + 5) > 0.82)) else 1)
                else:
                    sc.put(x, y, wall, 2 if n > 0.68 else 1 + (1 if n > 0.35 and y > top + 40 else 0))
    for x in range(W):                                                         # stalactites hanging from the ceiling
        if random.Random(seed * 31 + x // 7).random() < 0.5 and x % 7 == 3:
            ln = random.Random(seed + x).randint(8, 30)
            base = int(top + 30 * (abs(x - 112) / 112) ** 2.2)
            for y in range(base - 4, base + ln):
                half = 3.5 * (1 - (y - base + 4) / (ln + 4))
                for dx in range(-int(half), int(half) + 1):
                    sc.put(x + dx, y, wall, 2 if dx < 0 else 1)
    for y in range(FLOOR, H):                                                  # the floor: flat-ish stone, lit at the lip
        for x in range(W):
            n = noise(x, y, 6, seed + 2)
            s = 3 if y == FLOOR else 2 if y < FLOOR + 3 else 1 + (1 if n > 0.7 else 0)
            if y >= FRONT:
                s = max(0, s - 1 - (y - FRONT) // 30)
            sc.put(x, y, floor, s)
    for k in range(10):                                                        # stalagmites and rubble at the floor's edges
        x = random.Random(seed + k * 7).choice((random.Random(k).randint(2, 40), random.Random(k + 1).randint(185, 222)))
        ht = random.Random(seed + k).randint(8, 26)
        for y in range(FLOOR - ht, FLOOR + 2):
            half = 4.5 * (y - FLOOR + ht) / ht
            for dx in range(-int(half), int(half) + 1):
                sc.put(x + dx, y, wall, 3 if dx < -half * 0.3 else 2)


# ============================================================================ Root Hollows
def roots_dress(sc, seed, variant):
    rnd = random.Random(seed)
    # big roots: across the ceiling, snaking down the walls, a few breaking through the floor
    paths = [[(-10, 60), (40, 84), (90, 70), (150, 92), (235, 74)],
             [(20, -4), (34, 60), (14, 140), (26, 240), (8, FLOOR + 4)],
             [(206, -4), (194, 80), (214, 170), (198, 260), (216, FLOOR + 4)]]
    if variant == "a":
        paths.append([(112, 60), (120, 140), (104, 220), (116, FLOOR + 2)])         # a root column at the back
    else:
        paths += [[(70, 66), (60, 120), (80, 150)], [(160, 72), (176, 130), (150, 170)]]
        for y in range(180, FLOOR):                                            # a dark tunnel mouth in the back wall
            for x in range(80, 146):
                if ((x - 113) / 33) ** 2 + ((y - FLOOR) / 150) ** 2 <= 1:
                    sc.put(x, y, "cave", 0)
    for i, pts in enumerate(paths):
        root(sc, pts, rnd.randint(12, 18), rnd.randint(5, 8), seed + i)
    for k in range(10):                                                        # thin rootlets hanging down
        x0 = rnd.randint(10, 215)
        y0 = rnd.randint(70, 100)
        root(sc, [(x0, y0), (x0 + rnd.randint(-6, 6), y0 + rnd.randint(10, 25)), (x0 + rnd.randint(-8, 8), y0 + rnd.randint(28, 50))], 3, 1, k)
    for k in range(9):                                                         # clusters of glowing fungi
        cx = rnd.choice((rnd.randint(8, 60), rnd.randint(165, 218)))
        cy = rnd.choice((rnd.randint(120, 300), FLOOR - 1))
        kind = rnd.choice(("fungt", "fungt", "fungp"))
        for j in range(rnd.randint(2, 4)):
            x, h = cx + j * 4 - 4, rnd.randint(3, 7)
            for y in range(cy - h, cy + 1):
                sc.put(x, y, "root", 3)
            sc.disc(x, cy - h, 2.6, 1.6, kind, 2)
            sc.fix(x - 1, cy - h - 1, "fung0" if kind == "fungt" else "fungp0")
        sc.lights.append((cx, cy - 4, 28, 0.9))
    for k in range(6):                                                         # water dripping from the ceiling
        x = rnd.randint(30, 195)
        y0 = rnd.randint(90, 110)
        for y in range(y0, y0 + rnd.randint(4, 12), 2):
            sc.fix(x, y, "drop2")
        sc.fix(x, y0 + 22, "drop")
        sc.fix(x, FLOOR + 2, "drop2")
    if variant == "a":                                                         # a shallow pool on the floor
        for y in range(FLOOR + 6, FLOOR + 14):
            for x in range(130, 200):
                if ((x - 165) / 35) ** 2 + ((y - FLOOR - 10) / 4) ** 2 <= 1:
                    sc.put(x, y, "water", 2 if y < FLOOR + 9 else 1)


def treasure_dress(sc, seed, ramp_pedestal="cave"):
    # A stone pedestal in the middle with a pool of warm light, coins scattered across the floor.
    px = 112
    sc.box(px - 22, FLOOR - 10, px + 22, FLOOR, ramp_pedestal, 3)
    sc.box(px - 16, FLOOR - 26, px + 16, FLOOR - 10, ramp_pedestal, 2)
    sc.box(px - 20, FLOOR - 30, px + 20, FLOOR - 26, ramp_pedestal, 3)
    rnd = random.Random(seed)
    for k in range(34):
        x = int(px + rnd.gauss(0, 34))
        y = FLOOR + rnd.randint(1, 30)
        if 0 <= x < W:
            sc.fix(x, y, "coin")
            if k % 3 == 0:
                sc.fix(x + 1, y, "coinhi")
    for k in range(10):                                                        # a few coins on the pedestal steps
        sc.fix(px - 18 + k * 4, FLOOR - 11, "coin")
    sc.lights.append((px, FLOOR - 40, 110, 1.6))


def roots_boss(sc, seed):
    # The heart-root: great roots pour in from the ceiling and walls and knot together into one mass at
    # the back of the vault, an ember heart glowing in its middle; roots writhe out over the floor.
    rnd = random.Random(seed)
    hx, hy = 112, 200
    starts = [(x, 30) for x in range(10, 225, 30)] + [(0, y) for y in (90, 150, 230)] + [(224, y) for y in (80, 160, 240)]
    for i, (sx, sy) in enumerate(starts):
        mid = ((sx + hx) / 2 + rnd.uniform(-25, 25), (sy + hy) / 2 + rnd.uniform(-20, 20))
        root(sc, [(sx, sy), mid, (hx + (sx - hx) * 0.15, hy + (sy - hy) * 0.15)], rnd.uniform(10, 16), rnd.uniform(14, 18), i)
    sc.disc(hx, hy, 30, 34, "root", 2)
    for k in range(8):                                                         # knotted lumps on the mass
        a = math.radians(k * 45 + 20)
        sc.disc(hx + 20 * math.cos(a), hy + 24 * math.sin(a), 9, 8, "root", 2)
    for y in range(hy - 18, hy + 19):                                          # the ember heart
        for x in range(hx - 14, hx + 15):
            d = math.hypot((x - hx) / 12, (y - hy) / 16)
            if d < 1:
                sc.put(x, y, "heart", 4 if d < 0.3 else 3 if d < 0.65 else 2)
    for k in range(7):                                                         # glowing cracks running out from the heart
        a = math.radians(k * 51 + 10)
        x, y = hx, hy
        for t in range(30):
            x += math.cos(a + math.sin(t * 0.5) * 0.4) * 1.1
            y += math.sin(a + math.sin(t * 0.5) * 0.4) * 1.3
            if 14 < math.hypot(x - hx, y - hy) and sc.mat[int(y)][int(x)] and sc.mat[int(y)][int(x)][0] == "root":
                sc.fix(x, y, "ember" if t < 20 else "ember0")
    for i, pts in enumerate(([(hx - 10, hy + 30), (70, 290), (20, FLOOR + 4)], [(hx + 10, hy + 30), (160, 296), (220, FLOOR)],
                             [(hx, hy + 32), (104, 300), (96, FLOOR + 8)], [(hx - 20, hy + 20), (40, 250), (6, 300)])):
        root(sc, pts, 16, 7, 40 + i)
    sc.lights += [(hx, hy, 150, 2.0)]



# ============================================================================ Crystal Caverns
def crystal_cluster(sc, cx, base, size, seed, ramp="crys", up=True):
    # A spray of jagged crystal prisms growing from one point, each lit on its left facet.
    rnd = random.Random(seed)
    for k in range(rnd.randint(3, 6)):
        ang = math.radians((-90 if up else 90) + rnd.uniform(-38, 38))
        ln = size * rnd.uniform(0.55, 1.0)
        wd = max(2.5, size * rnd.uniform(0.14, 0.24))
        tip = (cx + ln * math.cos(ang), base + ln * math.sin(ang))
        nx, ny = -math.sin(ang), math.cos(ang)
        b1 = (cx + nx * wd, base + ny * wd)
        b2 = (cx - nx * wd, base - ny * wd)
        m1 = (b1[0] + (tip[0] - b1[0]) * 0.8, b1[1] + (tip[1] - b1[1]) * 0.8)
        m2 = (b2[0] + (tip[0] - b2[0]) * 0.8, b2[1] + (tip[1] - b2[1]) * 0.8)
        sc.poly([b1, m1, tip, ((b1[0] + b2[0]) / 2, (b1[1] + b2[1]) / 2)], ramp, 3)
        sc.poly([((b1[0] + b2[0]) / 2, (b1[1] + b2[1]) / 2), tip, m2, b2], ramp, 2)
        sc.fix(tip[0], tip[1] + (1 if up else -1), "crys0" if ramp == "crys" else "crys1")
    sc.lights.append((cx, base - size * 0.4 * (1 if up else -1), size * 2.4, 0.9))


def crystal_dress(sc, seed, variant):
    rnd = random.Random(seed)
    for k in range(7):                                                          # crystals hanging from the ceiling
        x = 15 + k * 32 + rnd.randint(-8, 8)
        crystal_cluster(sc, x, 76 + int(30 * (abs(x - 112) / 112) ** 2.2), rnd.randint(14, 26), seed + k, "crysd", up=False)
    for x, size in ((14, 46), (210, 50), (40, 22), (186, 26)):                  # big clusters on the walls and floor
        crystal_cluster(sc, x, FLOOR, size, seed + x)
    if variant == "a":
        for x in (80, 150):
            crystal_cluster(sc, x, 240, 18, seed + x * 3)
    else:                                                                       # one great crystal growing at the back
        crystal_cluster(sc, 112, FLOOR - 4, 110, seed + 99)
    for k in range(40):                                                         # glinting specks in the rock
        x, y = rnd.randint(4, 220), rnd.randint(80, 320)
        if sc.mat[y][x] and sc.mat[y][x][0] == "cstone":
            sc.fix(x, y, "crys1")


def crystal_boss(sc, seed):
    # A vast geode: the back wall split open into a ring of giant crystals around a cracked, blazing core.
    rnd = random.Random(seed)
    cx, cy = 112, 196
    for y in range(cy - 80, cy + 81):
        for x in range(W):
            d = math.hypot((x - cx) / 96, (y - cy) / 80)
            if d < 1:
                sc.put(x, y, "cstone", 0 if d < 0.8 else 1)
    for k in range(14):                                                         # crystals jutting inwards, uneven
        a = math.radians(k * 25.7 + rnd.uniform(-9, 9))
        bx, by = cx + 92 * math.cos(a), cy + 76 * math.sin(a)
        ang = math.degrees(math.atan2(cy - by, cx - bx)) + rnd.uniform(-25, 25)
        size = rnd.randint(22, 58)
        tip = (bx + size * math.cos(math.radians(ang)), by + size * math.sin(math.radians(ang)))
        wd = rnd.uniform(5, 10)
        nx, ny = -math.sin(math.radians(ang)) * wd, math.cos(math.radians(ang)) * wd
        sc.poly([(bx + nx, by + ny), tip, (bx, by)], "crys", 3)
        sc.poly([(bx, by), tip, (bx - nx, by - ny)], "crys", 2)
    sc.disc(cx, cy, 14, 14, "crys", 4, shade=False)
    for k in range(8):
        a = math.radians(k * 45)
        for t in range(14, 26):
            sc.fix(cx + t * math.cos(a), cy + t * math.sin(a), "crys0")
    for x, size in ((10, 60), (214, 64), (60, 30), (170, 34)):
        crystal_cluster(sc, x, FLOOR, size, seed + x)
    sc.lights.append((cx, cy, 170, 2.0))


# ============================================================================ Sunken Ruins
def masonry(sc, x0, x1, y0, y1, seed):
    for y in range(y0, y1):
        course = (y - y0) // 14
        for x in range(x0, x1):
            off = (course % 2) * 12
            joint = (y - y0) % 14 == 0 or (x - x0 + off) % 24 == 0
            blk = random.Random(seed + course * 31 + (x - x0 + off) // 24).random()
            sc.put(x, y, "mason", 0 if joint else 2 if blk < 0.3 else 1)


def column(sc, x, top, bot, broken=False, seed=0):
    rnd = random.Random(seed)
    for y in range(top, bot):
        for dx in range(-9, 10):
            s_ = 3 if dx < -4 else 2 if dx < 3 else 1
            if abs(dx) in (3, 7) and y % 3:
                s_ -= 1                                                          # fluting
            sc.put(x + dx, y, "statue", s_)
    if broken:
        for dx in range(-9, 10):
            for y in range(top, top + rnd.randint(0, 9)):
                sc.put(x + dx, y, "mason", 1)
    else:
        sc.box(x - 13, top - 8, x + 13, top, "statue", 3)
    sc.box(x - 12, bot - 6, x + 12, bot, "statue", 2)


def glyph_band(sc, y, seed, x0=10, x1=215):
    rnd = random.Random(seed)
    for x in range(x0, x1, 9):
        shape = rnd.choice((((0, 0), (0, 1), (0, 2), (1, 1)), ((0, 0), (1, 1), (2, 2), (0, 2), (2, 0)), ((1, 0), (0, 1), (2, 1), (1, 2)),
                            ((0, 0), (1, 0), (2, 0), (1, 1), (1, 2))))
        for dx, dy in shape:
            sc.fix(x + dx, y + dy, "glyph0" if rnd.random() < 0.3 else "glyph1")
    sc.lights.append(((x0 + x1) / 2, y, 140, 0.4))


def statue(sc, x, base, scale=1.0, headless=True):
    # A broken statue of an old hero: a robed figure on a plinth, arms lost, often missing its head.
    S = scale
    sc.box(x - 16 * S, base - 10 * S, x + 16 * S, base, "statue", 2)
    sc.poly([(x - 11 * S, base - 10 * S), (x + 11 * S, base - 10 * S), (x + 7 * S, base - 58 * S), (x - 7 * S, base - 58 * S)], "statue", 2)
    sc.poly([(x - 7 * S, base - 58 * S), (x + 7 * S, base - 58 * S), (x + 12 * S, base - 66 * S), (x - 12 * S, base - 66 * S)], "statue", 3)
    if not headless:
        sc.disc(x, base - 74 * S, 6 * S, 7 * S, "statue", 3)
    else:
        sc.poly([(x - 4 * S, base - 66 * S), (x + 3 * S, base - 66 * S), (x + 1 * S, base - 70 * S)], "statue", 2)
    for k in range(5):
        sc.put(x - 6 * S + k * 3 * S, base - 30 * S, "statue", 1)


def ruins_dress(sc, seed, variant):
    masonry(sc, 0, W, 60, FLOOR, seed)
    glyph_band(sc, 118, seed)
    if variant == "a":                                                          # a colonnade
        for i, x in enumerate((30, 84, 140, 194)):
            column(sc, x, 132 if i % 3 else 160, FLOOR, broken=(i % 3 != 0), seed=seed + x)
    else:                                                                       # an archway and a broken statue
        for y in range(150, FLOOR):
            for x in range(70, 156):
                if ((x - 113) / 40) ** 2 + ((y - FLOOR) / 160) ** 2 <= 1:
                    sc.put(x, y, "mason", 0)
        statue(sc, 32, FLOOR, 1.0)
        statue(sc, 196, FLOOR, 0.9, headless=False)
    for k in range(12):                                                         # moss and roots creeping over the stone
        x, y = random.Random(seed + k).randint(5, 220), random.Random(seed + k * 7).randint(70, 300)
        for j in range(18):
            sc.put(x + j % 5 - 2, y + j // 5, "grass", 2 if j % 3 else 1)
    for y in range(FLOOR + 4, FLOOR + 22):                                      # standing water: the ruins are sunken
        for x in range(W):
            if noise(x, y * 3, 14, seed) > 0.55:
                sc.put(x, y, "pool", 2 if y < FLOOR + 8 else 1)


def ruins_boss(sc, seed):
    # A grand drowned hall: a colossal seated statue at the back (headless, hands on its knees), a great
    # rune circle glowing faintly behind it, broken columns either side, water across the floor.
    masonry(sc, 0, W, 46, FLOOR, seed)
    cx, cy = 112, 150
    for a10 in range(0, 3600, 4):                                               # the rune circle
        a = math.radians(a10 / 10)
        for r, key in ((62, "glyph1"), (54, "glyph1")):
            sc.fix(cx + r * math.cos(a), cy + r * 0.9 * math.sin(a), key)
    for k in range(16):
        a = math.radians(k * 22.5)
        for t in range(55, 62):
            sc.fix(cx + t * math.cos(a), cy + t * 0.9 * math.sin(a), "glyph0")
    sc.box(60, 250, 164, FLOOR, "statue", 2)                                    # throne block
    sc.poly([(78, 250), (146, 250), (138, 150), (86, 150)], "statue", 2)         # the body
    sc.poly([(70, 150), (154, 150), (146, 132), (78, 132)], "statue", 3)         # shoulders
    sc.box(66, 228, 96, 252, "statue", 3)                                       # knees and hands
    sc.box(128, 228, 158, 252, "statue", 3)
    sc.poly([(104, 132), (118, 132), (114, 126)], "statue", 2)                  # the broken neck
    for x in (14, 210):
        column(sc, x, 120, FLOOR, broken=True, seed=seed + x)
    glyph_band(sc, 96, seed + 3)
    for y in range(FLOOR + 2, FLOOR + 30):
        for x in range(W):
            if noise(x, y * 3, 16, seed + 1) > 0.42:
                sc.put(x, y, "pool", 3 if y < FLOOR + 6 else 2)
    sc.lights += [(cx, cy, 160, 1.2)]


# ============================================================================ Hollow Deep
def smoke_bands(sc, seed, y0, y1, density=0.56):
    # Drifting smoke as a thin haze: a sparse dither of dark grey, a little denser in the middle of a wisp.
    for y in range(y0, y1):
        for x in range(W):
            n = noise(x, y * 3, 26, seed)
            if n > density and ((x + y) % 2 == 0 or n > density + 0.14) and (x * 3 + y) % 3:
                sc.fix(x, y, "smoke1" if n < density + 0.1 else "smoke2")


def deep_dress(sc, seed, variant):
    rnd = random.Random(seed)
    for k in range(5):                                                          # cracked obsidian pillars
        x = 20 + k * 46 + rnd.randint(-6, 6)
        top = rnd.randint(60, 120)
        for y in range(top, FLOOR):
            for dx in range(-7, 8):
                sc.put(x + dx, y, "black", 3 if dx < -3 else 2 if dx < 3 else 1)
        for t in range(rnd.randint(30, 80)):                                    # a sickly-lit crack down it
            sc.fix(x + int(2 * math.sin(t / 4)), top + 10 + t * 2, "sick1" if t % 5 else "sick0")
    if variant == "b":                                                          # chains hanging from the dark, a black gate
        for x in (60, 92, 140, 170):
            ln = rnd.randint(80, 160)
            for y in range(60, 60 + ln):
                sc.put(x + (1 if (y // 3) % 2 else 0), y, "chain", 3 if y % 3 == 0 else 2)
        for y in range(190, FLOOR):
            for x in range(86, 140):
                if ((x - 113) / 27) ** 2 + ((y - FLOOR) / 140) ** 2 <= 1:
                    bar = (x - 86) % 7 == 0
                    sc.put(x, y, "chain" if bar else "black", 3 if bar else 0)
    for k in range(4):                                                          # tattered banners
        x = rnd.choice((rnd.randint(40, 70), rnd.randint(150, 185)))
        for y in range(80, 80 + rnd.randint(40, 70)):
            for dx in range(-5, 6):
                if y < 120 or (dx + y) % 5:
                    sc.put(x + dx, y, "rag", 2 if dx < 0 else 1)
    smoke_bands(sc, seed, 250, FLOOR + 6, 0.6)
    smoke_bands(sc, seed + 5, 110, 150, 0.66)
    for k in range(4):                                                          # sickly green braziers
        x = (24, 200, 66, 158)[k]
        sc.box(x - 4, FLOOR - 14, x + 4, FLOOR, "black", 2)
        for y in range(FLOOR - 24, FLOOR - 14):
            t = (FLOOR - 14 - y) / 10
            for dx in range(-3, 4):
                if abs(dx) < 3.5 * (1 - t):
                    sc.fix(x + dx, y, "sick0" if t > 0.5 and dx == 0 else "sick1")
        sc.lights.append((x, FLOOR - 20, 60, 1.0))


def deep_boss(sc, seed):
    # The Hollow King's throne hall: a throne of black iron spikes on a stepped dais, sickly fire either
    # side, smoke rolling over the floor, the King stands before it (spot "boss").
    for y in range(100, FLOOR):                                                 # the dais steps
        pass
    for k, (w_, h_) in enumerate(((90, 10), (70, 10), (52, 10))):
        sc.box(150 - w_ // 2 + 20, FLOOR - h_ * (k + 1), 150 + w_ // 2 + 20, FLOOR - h_ * k, "black", 3 - k % 2)
    tx = 172
    for k in range(9):                                                          # the spiked throne back
        x = tx - 32 + k * 8
        ht = 70 + 40 * math.sin(math.pi * k / 8)
        sc.poly([(x - 4, FLOOR - 30), (x + 4, FLOOR - 30), (x, FLOOR - 30 - ht)], "chain", 3 if k < 4 else 2)
        sc.fix(x, FLOOR - 30 - ht + 1, "sick0")
        for t in range(int(ht * 0.6)):
            sc.fix(x - 3 + t * 3 / ht, FLOOR - 31 - t, "sick1") if k == 4 else None
    sc.box(tx - 22, FLOOR - 52, tx + 22, FLOOR - 30, "chain", 2)
    sc.lights.append((tx, FLOOR - 70, 90, 0.8))
    for k in range(6):
        sc.fix(tx - 20 + k * 8, FLOOR - 40, "sick1")
    for x in (40, 108):                                                         # great braziers
        sc.box(x - 8, FLOOR - 30, x + 8, FLOOR, "black", 2)
        for y in range(FLOOR - 60, FLOOR - 30):
            t = (FLOOR - 30 - y) / 30
            for dx in range(-7, 8):
                if abs(dx) < 7.5 * (1 - t) * (0.7 + 0.3 * math.sin(y * 0.7)):
                    sc.fix(x + dx, y, "sick0" if t > 0.5 and abs(dx) < 2 else "sick1")
        sc.lights.append((x, FLOOR - 44, 110, 1.6))
    smoke_bands(sc, seed, 270, FLOOR + 14, 0.56)
    smoke_bands(sc, seed + 9, 90, 130, 0.64)
    for k in range(5):                                                          # tattered banners of the Hollow
        x = 20 + k * 46
        for y in range(56, 56 + 90 - (k % 2) * 30):
            for dx in range(-6, 7):
                if y < 110 or (dx + y) % 4:
                    sc.put(x + dx, y, "rag", 2 if dx < 0 else 1)
        sc.fix(x, 76, "sick0")


ZONES = {"roots":   dict(dress=roots_dress, boss=roots_boss, light=[(112, 160, 170, 0.35)], wall="cave", floor="cavef"),
         "crystal": dict(dress=crystal_dress, boss=crystal_boss, light=[(112, 160, 170, 0.3)], wall="cstone", floor="cfloor", calm=True),
         "ruins":   dict(dress=ruins_dress, boss=ruins_boss, light=[(112, 180, 200, 0.5)], wall="mason", floor="mfloor"),
         "deep":    dict(dress=deep_dress, boss=deep_boss, light=[], wall="black", floor="bfloor", calm=True)}


def room(zone, kind, seed):
    z = ZONES[zone]
    sc = Scene(f"{zone}_{kind}")
    cave_shell(sc, seed, vault=(kind == "boss"), wall=z["wall"], floor=z["floor"], calm=z.get("calm", False))
    sc.lights = list(z["light"])
    if kind == "boss":
        z["boss"](sc, seed)
    else:
        z["dress"](sc, seed, "b" if kind == "fight_b" else "a")
    if kind == "treasure":
        treasure_dress(sc, seed, z["wall"])
    sc.spots = {"skerbie": [56, FLOOR], "enemies": [[162, FLOOR], [190, FLOOR], [140, FLOOR]], "floor": FLOOR,
                "buttons_top": FRONT}
    if kind == "treasure":
        sc.spots["chest_spot"] = [112, FLOOR - 30]
    if kind == "boss":
        sc.spots["boss"] = [168, FLOOR]
    sc.write()


def stairs():
    # Descending-stairs transition [6]: looking down a stone stairwell; the steps come up towards the view
    # (one step per loop) as he walks down, the far end lost in darkness, a torch on each wall passing by.
    frames = []
    HZ = 150                                                                    # the vanishing line, far down the stairs
    for f in range(6):
        g = {}
        phase = f / 6
        for y in range(H):
            z = max(0.01, (y - HZ) / (H - HZ))                                  # 1 at the bottom (close), 0 at HZ (far)
            depth = 1 / z
            k = depth * 3.2 + phase                                             # step coordinate
            fk = k % 1
            half = 40 + 90 * z                                                  # the stairwell narrows into the distance
            for x in range(W):
                if y < HZ:
                    c = "#17151c"
                elif abs(x - 112) > half:                                       # the side walls, rough stone
                    wall = (int(x * 0.7 + depth * 9) + int(depth * 6)) % 5
                    c = "#23212b" if wall else "#2a2036"
                else:
                    c = "#4a3a5c" if fk < 0.12 else "#3a2d4a" if fk < 0.3 else "#2a2036" if fk < 0.7 else "#23212b"
                fade = 1 - z                                                    # darkness swallowing the far steps
                if fade > 0.55 + ((x * 7 + y * 13) % 16) / 40:
                    c = "#17151c"
                g[(x, y)] = c
        for side in (-1, 1):                                                    # wall torches sliding past
            ty = int(250 + phase * 200)
            tx = 112 + side * (40 + 90 * (ty - HZ) / (H - HZ)) - side * 4
            for dy in range(-8, 1):
                for dx in range(-2, 3):
                    if abs(dx) * 3 <= -dy + 1:
                        g[(int(tx + dx), ty + dy)] = "#ffd08a" if abs(dx) < 1 and dy < -2 else "#ffb35c"
            for dy in range(1, 6):
                if ty + dy < H:
                    g[(int(tx), ty + dy)] = "#3b2a22"
        frames.append(g)
    pal, inv, anim = {}, {}, []
    chars = iter("abcdefghijklmnopqrstuvwxyz")
    for g in frames:
        rows = []
        for y in range(H):
            line = ""
            for x in range(W):
                c = g[(x, y)]
                if c not in inv:
                    inv[c] = next(chars)
                    pal[inv[c]] = c
                line += inv[c]
            rows.append(line)
        anim.append(rows)
    json.dump({"width": W, "height": H, "fps": 10, "palette": pal, "dye_zones": {}, "attach": {},
               "animations": {"descend": anim}}, open(f"{bs.OUT}/stairs.json", "w"))
    print("wrote stairs")


if __name__ == "__main__":
    todo = sys.argv[1:] or list(ZONES) + ["stairs"]
    for z in todo:
        if z == "stairs":
            stairs()
            continue
        for i, kind in enumerate(("fight_a", "fight_b", "treasure", "boss")):
            room(z, kind, sum(map(ord, z)) + i * 17)
