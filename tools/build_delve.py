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
})
bs.FIXED.update({"drop": "#8ff0e6", "drop2": "#2ec4b6", "coin": "#f2c14e", "coinhi": "#ffe08a",
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


def cave_shell(sc, seed, vault=False):
    # Solid rock everywhere, a chamber hollowed out of it: an arched back wall, a floor, a foreground lip.
    top = 46 if vault else 70
    for y in range(H):
        for x in range(W):
            n = noise(x, y, 9, seed)
            sc.put(x, y, "cave", 1 if n > 0.6 else 0)
    for y in range(top, FLOOR + 1):                                            # the hollow: a lighter back wall
        for x in range(W):
            edge = 18 * (1 - ((y - top) / (FLOOR - top))) ** 0.5 if not vault else 8 * (1 - ((y - top) / (FLOOR - top)))
            arch = top + 30 * (abs(x - 112) / 112) ** 2.2
            if y > arch and edge < x < W - edge:
                n = noise(x, y, 7, seed + 1)
                sc.put(x, y, "cave", 2 if n > 0.68 else 1 + (1 if n > 0.35 and y > top + 40 else 0))
    for x in range(W):                                                         # stalactites hanging from the ceiling
        if random.Random(seed * 31 + x // 7).random() < 0.5 and x % 7 == 3:
            ln = random.Random(seed + x).randint(8, 30)
            base = int(top + 30 * (abs(x - 112) / 112) ** 2.2)
            for y in range(base - 4, base + ln):
                half = 3.5 * (1 - (y - base + 4) / (ln + 4))
                for dx in range(-int(half), int(half) + 1):
                    sc.put(x + dx, y, "cave", 2 if dx < 0 else 1)
    for y in range(FLOOR, H):                                                  # the floor: flat-ish stone, lit at the lip
        for x in range(W):
            n = noise(x, y, 6, seed + 2)
            s = 3 if y == FLOOR else 2 if y < FLOOR + 3 else 1 + (1 if n > 0.7 else 0)
            if y >= FRONT:
                s = max(0, s - 1 - (y - FRONT) // 30)
            sc.put(x, y, "cavef", s)
    for k in range(10):                                                        # stalagmites and rubble at the floor's edges
        x = random.Random(seed + k * 7).choice((random.Random(k).randint(2, 40), random.Random(k + 1).randint(185, 222)))
        ht = random.Random(seed + k).randint(8, 26)
        for y in range(FLOOR - ht, FLOOR + 2):
            half = 4.5 * (y - FLOOR + ht) / ht
            for dx in range(-int(half), int(half) + 1):
                sc.put(x + dx, y, "cave", 3 if dx < -half * 0.3 else 2)


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


ZONES = {"roots": dict(dress=roots_dress, boss=roots_boss, light=[(112, 160, 170, 0.35)])}


def room(zone, kind, seed):
    z = ZONES[zone]
    sc = Scene(f"{zone}_{kind}")
    cave_shell(sc, seed, vault=(kind == "boss"))
    sc.lights = list(z["light"])
    if kind == "boss":
        z["boss"](sc, seed)
    else:
        z["dress"](sc, seed, "b" if kind == "fight_b" else "a")
    if kind == "treasure":
        treasure_dress(sc, seed)
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
