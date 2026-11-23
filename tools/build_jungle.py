# Builds the Jungle Run art (ART_BRIEF §10), landscape 487x225.
# Usage: python tools/build_jungle.py [twilight ...]
#        then render each art/source/jungle/<biome>/<name>.json with tools/render.py
#
# Per biome:
#   sky.json      layer 0, opaque: the sky gradient, clouds, a moon
#   far.json      layer 1: distant canopy silhouettes (transparent above)
#   mid.json      layer 2: tree trunks, hanging vines, leaf clumps
#   fore.json     layer 3: big foreground leaves and vines at the top and bottom edges (fast parallax)
#   tiles.json    16x16 terrain tiles as one "tiles" row; "tile_names" lists them in order
# Every layer is a seamless horizontal loop exactly 487 px wide: all the noise is built from sine waves
# with whole-number frequencies over 487 px, and every feature is drawn at x, x-487 and x+487, so the
# right edge runs straight into the left edge. Backgrounds have no hard outlines; light from the top-left.
# Colours are from the §3 palette.
import json, math, os, random, sys

W, H, T = 487, 225, 16
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]

BIOMES = {
    "twilight": dict(
        sky=["#2a2036", "#3a2d4a", "#4a3a5c", "#f2a0b0", "#ffc8a8"],     # top -> horizon
        cloud=["#4a3a5c", "#f2a0b0"], moon=["#ffc8a8", "#f2a0b0"], stars="#ffc8a8",
        far=["#23212b", "#2a2036", "#4a3a5c"],
        midtrunk=["#17151c", "#23212b", "#2a2036", "#3b2a22"],
        leaf=["#17151c", "#1f3d44", "#2c4234", "#3e5a46", "#557a5c"],
        trunk=["#17151c", "#23212b", "#3b2a22", "#7a5636"],
        vine=["#2c4234", "#3e5a46", "#557a5c"],
        fore=["#17151c", "#1f3d44", "#2c4234"],
        soil=["#17151c", "#23212b", "#2a2036", "#3a2d4a", "#4a3a5c"],
        grass=["#1f3d44", "#2c4234", "#3e5a46", "#557a5c", "#a8945e"],
        rock=["#23212b", "#3b4a63", "#4d5e7a"],
        bloom=["#f2a0b0", "#ffc8a8"], cap=["#ffc8a8", "#f2a0b0", "#4a3a5c"], bone=["#bfae8c", "#8b7a4a"],
        glow="#ffd08a",
    ),
}


def pnoise(x, y, seed, octaves=((3, 1.0), (7, 0.5), (17, 0.25)), yscale=0.05):
    # Smooth noise that repeats exactly every W pixels in x (sums of sines with whole-number frequencies).
    rnd = random.Random(seed)
    v, tot = 0.0, 0.0
    for f, amp in octaves:
        p1, p2, p3 = rnd.random() * 6.283, rnd.random() * 6.283, rnd.random() * 6.283
        v += amp * (math.sin(2 * math.pi * f * x / W + p1 + y * yscale * f * 0.7) * 0.6 +
                    math.sin(2 * math.pi * (f + 1) * x / W + p2 - y * yscale * f * 0.4) * 0.4 +
                    0.3 * math.sin(y * yscale * f + p3))
        tot += amp * 1.3
    return 0.5 + 0.5 * v / tot


class Layer:
    def __init__(self, w=W, h=H):
        self.w, self.h = w, h
        self.px = {}

    def put(self, x, y, col, wrap=True):
        x, y = int(x), int(y)
        if wrap:
            x %= self.w
        if 0 <= x < self.w and 0 <= y < self.h and col:
            self.px[(x, y)] = col

    def get(self, x, y):
        return self.px.get((int(x) % self.w, int(y)))

    def disc(self, cx, cy, rx, ry, ramp, wrap=True, lit=True):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                dx, dy = (x + .5 - cx) / rx, (y + .5 - cy) / ry
                if dx * dx + dy * dy <= 1:
                    l = dx * -0.6 + dy * -0.8
                    i = (len(ramp) - 1) if (lit and l > 0.5) else max(0, len(ramp) - 2 if l > -0.2 else len(ramp) - 3) if lit else 0
                    self.put(x, y, ramp[min(len(ramp) - 1, i)], wrap)

    def line(self, pts, w0, w1, ramp, wrap=True):
        seg = []
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            n = max(2, int(math.hypot(x1 - x0, y1 - y0)))
            seg += [(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n) for k in range(n)]
        for k, (cx, cy) in enumerate(seg):
            r = (w0 + (w1 - w0) * k / max(1, len(seg) - 1)) / 2
            for y in range(int(cy - r) - 1, int(cy + r) + 2):
                for x in range(int(cx - r) - 1, int(cx + r) + 2):
                    if math.hypot(x + .5 - cx, y + .5 - cy) <= r:
                        l = ((x + .5 - cx) * -0.6 + (y + .5 - cy) * -0.8) / max(r, .5)
                        i = len(ramp) - 1 if l > 0.45 else len(ramp) - 2 if l > -0.4 else max(0, len(ramp) - 3)
                        self.put(x, y, ramp[i], wrap)

    def json(self, path, name="layer", frames=None, extra=None):
        frames = frames or [self]
        pal, inv = {}, {}
        chars = iter("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&*+-=?@^_~")
        rows_all = []
        for fr in frames:
            rows = []
            for y in range(fr.h):
                line = []
                for x in range(fr.w):
                    c = fr.px.get((x, y))
                    if c is None:
                        line.append(".")
                        continue
                    if c not in inv:
                        inv[c] = next(chars)
                        pal[inv[c]] = c
                    line.append(inv[c])
                rows.append("".join(line))
            rows_all.append(rows)
        d = {"width": frames[0].w, "height": frames[0].h, "fps": 8, "palette": pal, "dye_zones": {}, "attach": {},
             "animations": {name: rows_all}}
        d.update(extra or {})
        os.makedirs(os.path.dirname(path), exist_ok=True)
        json.dump(d, open(path, "w"))
        print("wrote", path, len(pal), "colours")


def dither_pick(ramp, v, x, y):
    # v in [0, len-1]: pick between neighbouring ramp colours with a Bayer threshold.
    v = max(0.0, min(len(ramp) - 1.0, v))
    i = int(v)
    if i >= len(ramp) - 1:
        return ramp[-1]
    return ramp[i + 1] if (v - i) > (BAYER[y % 4][x % 4] + 0.5) / 16 else ramp[i]


# ============================================================================ layers
def sky(b, seed):
    L = Layer()
    for y in range(H):
        t = (y / (H * 0.78)) ** 1.15 * (len(b["sky"]) - 1)
        for x in range(W):
            L.put(x, y, dither_pick(b["sky"], t, x, y), wrap=False)
    for y in range(10, 120):                                                    # long soft cloud bands
        for x in range(W):
            n = pnoise(x, y * 3, seed + 1, octaves=((2, 1), (5, 0.5), (11, 0.3)), yscale=0.02)
            band = math.exp(-((y - 70 - 25 * math.sin(2 * math.pi * x / W * 2)) / 22) ** 2)
            if n * band > 0.45:
                L.put(x, y, b["cloud"][1] if n * band > 0.56 and y > 60 else b["cloud"][0], wrap=False)
    rnd = random.Random(seed)
    for k in range(70):                                                         # stars in the upper sky
        x, y = rnd.randrange(W), rnd.randrange(0, 60)
        if L.get(x, y) in (b["sky"][0], b["sky"][1]):
            L.put(x, y, b["stars"])
    mx, my = 360, 46                                                            # a big low moon
    for y in range(my - 16, my + 17):
        for x in range(mx - 16, mx + 17):
            d = math.hypot(x - mx, y - my)
            if d < 15:
                L.put(x, y, b["moon"][0] if d < 12 or (x - mx) + (y - my) < -6 else b["moon"][1])
    return L


def far(b, seed):
    L = Layer()
    for x in range(W):                                                          # a rolling line of distant crowns
        top = 96 + int(pnoise(x, 0, seed, octaves=((4, 1), (9, 0.7), (23, 0.5), (41, 0.3))) * 46 - 23)
        for y in range(top, H):
            v = 1.0 + (y - top) / 50 + (pnoise(x, y, seed + 3) - 0.5) * 0.6
            L.put(x, y, dither_pick(b["far"][1::-1], min(1, max(0, v - 1)), x, y))
    for x in range(W):                                                          # a lit rim along the crowns
        for y in range(60, H):
            if L.get(x, y) and not L.get(x, y - 1):
                L.put(x, y, b["far"][2])
                break
    return L


def mid(b, seed):
    L = Layer()
    rnd = random.Random(seed)
    n = 7
    for k in range(n):                                                          # trunks, evenly spread so it loops
        x0 = int((k + rnd.uniform(0.2, 0.8)) * W / n)
        wdt = rnd.randint(9, 15)
        lean = rnd.uniform(-6, 6)
        L.line([(x0 + lean, -4), (x0 + lean * 0.4, 110), (x0, H + 4)], wdt * 0.8, wdt * 1.25, b["midtrunk"])
        for (ry, side) in ((rnd.randint(150, 190), -1), (rnd.randint(150, 190), 1)):   # buttress roots
            L.line([(x0, ry), (x0 + side * wdt * 1.6, H + 2)], wdt * 0.6, 3, b["midtrunk"])
        for j in range(rnd.randint(2, 3)):                                      # hanging vines
            vx = x0 + rnd.uniform(-wdt * 2.5, wdt * 2.5)
            ln = rnd.randint(60, 140)
            pts = [(vx + 3 * math.sin(t / 9 + j), t) for t in range(0, ln, 6)]
            L.line(pts, 2, 2, b["vine"])
            for t in range(10, ln, 14):
                L.disc(vx + 3 * math.sin(t / 9 + j) + 2, t, 2.6, 1.6, b["leaf"][2:])
    for k in range(18):                                                         # leaf clumps hanging from the top
        cx, cy = (k + rnd.random()) * W / 18, rnd.randint(-6, 26)
        for j in range(4):
            L.disc(cx + rnd.uniform(-16, 16), cy + rnd.uniform(-6, 10), rnd.uniform(9, 15), rnd.uniform(6, 9), b["leaf"][1:4])
    return L


def fore(b, seed):
    L = Layer()
    rnd = random.Random(seed)

    def big_leaf(cx, cy, ang, ln, wd):
        a = math.radians(ang)
        ux, uy = math.cos(a), math.sin(a)
        for t in range(int(ln)):
            half = wd * math.sin(math.pi * t / ln) ** 0.8
            for s in range(-int(half), int(half) + 1):
                x = cx + ux * t - uy * s
                y = cy + uy * t + ux * s
                col = b["fore"][2] if s < -half * 0.3 else b["fore"][1] if s < half * 0.5 else b["fore"][0]
                if abs(s) < 0.8:
                    col = b["fore"][0]                                          # the midrib
                L.put(x, y, col)
    for k in range(6):                                                          # leaves fanning up from the bottom edge
        cx = (k + rnd.uniform(0.2, 0.8)) * W / 6
        for j in range(3):
            big_leaf(cx, H + 4, -90 + rnd.uniform(-50, 50), rnd.randint(26, 40), rnd.randint(6, 9))
    for k in range(5):                                                          # leaves drooping from the top edge
        cx = (k + rnd.uniform(0.2, 0.8)) * W / 5
        for j in range(2):
            big_leaf(cx, -4, 90 + rnd.uniform(-55, 55), rnd.randint(24, 36), rnd.randint(6, 8))
        vx = cx + rnd.uniform(-20, 20)                                          # a thick vine swag
        L.line([(vx + 3 * math.sin(t / 7), t) for t in range(0, rnd.randint(40, 70), 5)], 3, 3, b["fore"])
    return L


# ============================================================================ tiles
TILE_NAMES = ["top_left", "top_a", "top_b", "top_c", "top_right",
              "fill_a", "fill_b", "fill_c", "fill_left", "fill_right",
              "gap_left_top", "gap_right_top", "gap_left", "gap_right",
              "slope_up", "slope_down", "slope_up_low", "slope_up_high", "slope_down_high", "slope_down_low",
              "plat_left", "plat_mid", "plat_right",
              "deco_mushroom", "deco_mushrooms", "deco_bones", "deco_flower", "deco_flowers", "deco_tuft", "deco_rock"]


def tile(b, name, seed):
    L = Layer(T, T)
    soil, grass = b["soil"], b["grass"]
    rnd = random.Random(seed)

    def ground(surface, left_edge=False, right_edge=False, fill_only=False, xs=range(T)):
        for x in xs:
            top = surface(x)
            if top is None:
                continue
            for y in range(max(0, int(top)), T):
                d = y - top
                if fill_only:
                    v = 2 + (pnoise(x * 7 + seed, y * 7, seed) - 0.5) * 1.6
                    col = dither_pick(soil[1:], v - 1, x, y)
                elif d < 1:
                    col = grass[4] if x % 5 == 1 else grass[3]
                elif d < 3:
                    col = grass[2] if (x + y) % 4 else grass[3]
                elif d < 4:
                    col = grass[1] if x % 3 else soil[3]
                else:
                    v = 2 + (pnoise(x * 7 + seed, y * 7, seed) - 0.5) * 1.6
                    col = dither_pick(soil[1:], v - 1, x, y)
                L.put(x, y, col, wrap=False)
            for y in range(max(0, int(top)), T):
                if (left_edge and x == 0) or (right_edge and x == T - 1):
                    L.put(x, y, soil[0], wrap=False)
        if not fill_only:
            for x in xs:                                                        # grass blades poking up
                top = surface(x)
                if top is not None and x % 3 == (seed % 3) and top >= 1:
                    L.put(x, top - 1, grass[3], wrap=False)
        for k in range(2):                                                      # pebbles in the soil
            x, y = rnd.randint(2, 13), rnd.randint(8, 14)
            if L.px.get((x, y)) in soil:
                L.put(x, y, b["rock"][1], wrap=False)
                L.put(x + 1, y, b["rock"][0], wrap=False)

    flat = lambda x: 3
    if name.startswith("top_"):
        if name == "top_left":
            ground(lambda x: 3 if x > 1 else 5 - x, left_edge=True)
        elif name == "top_right":
            ground(lambda x: 3 if x < 14 else 3 + (x - 13), right_edge=True)
        else:
            ground(flat)
    elif name.startswith("fill_"):
        ground(lambda x: 0, fill_only=True, left_edge=name == "fill_left", right_edge=name == "fill_right")
        if name == "fill_c":                                                    # a root threading through
            for x in range(T):
                y = 8 + int(2 * math.sin(x / 3))
                L.put(x, y, b["trunk"][2], wrap=False)
                L.put(x, y + 1, b["trunk"][1], wrap=False)
    elif name in ("gap_left_top", "gap_right_top"):                             # the lip of a pit, roots dangling
        right = name == "gap_left_top"
        ground(lambda x: 3 if (x < 12 if right else x > 3) else None)
        edge = 11 if right else 4
        for y in range(3, T):
            L.put(edge, y, soil[0], wrap=False)
        for y in range(6, 15):
            L.put(edge + (1 if right else -1), y, b["trunk"][2] if y % 3 else None, wrap=False)
    elif name in ("gap_left", "gap_right"):
        right = name == "gap_left"
        ground(lambda x: 0 if (x < 12 if right else x > 3) else None, fill_only=True)
        edge = 11 if right else 4
        for y in range(T):
            L.put(edge, y, soil[0], wrap=False)
    elif name.startswith("slope"):
        f = {"slope_up": lambda x: 15 - x, "slope_down": lambda x: x,
             "slope_up_low": lambda x: 15 - x / 2, "slope_up_high": lambda x: 7 - x / 2,
             "slope_down_high": lambda x: x / 2, "slope_down_low": lambda x: 8 + x / 2}[name]
        ground(lambda x: max(0, f(x)))
    elif name.startswith("plat_"):                                              # a floating mossy log platform
        x0 = 2 if name == "plat_left" else 0
        x1 = 13 if name == "plat_right" else 15
        for x in range(x0, x1 + 1):
            for y in range(4, 11):
                col = b["trunk"][3] if y == 4 else b["trunk"][2] if y < 8 else b["trunk"][1]
                L.put(x, y, col, wrap=False)
            L.put(x, 3, grass[3] if x % 2 else grass[2], wrap=False)
            if x % 4 == 1:
                L.put(x, 11, b["vine"][1], wrap=False)
                L.put(x, 12, b["vine"][0], wrap=False)
        if name == "plat_left":
            for y in range(5, 10):
                L.put(1, y, b["trunk"][1], wrap=False)
            L.put(3, 7, b["trunk"][0], wrap=False)
        if name == "plat_right":
            for y in range(5, 10):
                L.put(14, y, b["trunk"][1], wrap=False)
    else:                                                                       # decor sits on a ground top (transparent)
        if name in ("deco_mushroom", "deco_mushrooms"):
            spots = [(8, 9)] if name == "deco_mushroom" else [(5, 11), (10, 9)]
            for (cx, cy) in spots:
                for y in range(cy, T):
                    L.put(cx, y, b["bone"][0], wrap=False)
                for x in range(cx - 3, cx + 4):
                    for y in range(cy - 3, cy + 1):
                        if (x - cx) ** 2 / 10 + (y - cy) ** 2 / 9 <= 1:
                            L.put(x, y, b["cap"][0] if x < cx and y < cy - 1 else b["cap"][1] if y < cy else b["cap"][2], wrap=False)
        elif name == "deco_bones":
            for x in range(3, 13):
                L.put(x, 13, b["bone"][0] if x % 4 else b["bone"][1], wrap=False)
            for (x, y) in ((2, 12), (2, 14), (13, 12), (13, 14)):
                L.put(x, y, b["bone"][0], wrap=False)
            for x in range(6, 11):                                              # a little skull
                for y in range(8, 12):
                    L.put(x, y, b["bone"][0] if y < 11 else b["bone"][1], wrap=False)
            L.put(7, 9, b["soil"][0], wrap=False)
            L.put(9, 9, b["soil"][0], wrap=False)
        elif name in ("deco_flower", "deco_flowers"):
            for (cx, cy) in ([(8, 7)] if name == "deco_flower" else [(4, 9), (9, 6), (13, 10)]):
                for y in range(cy + 1, T):
                    L.put(cx, y, grass[2], wrap=False)
                L.put(cx + 1, cy + 4, grass[3], wrap=False)
                for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
                    L.put(cx + dx, cy + dy, b["bloom"][0], wrap=False)
                L.put(cx, cy, b["bloom"][1], wrap=False)
        elif name == "deco_tuft":
            for x in range(3, 13):
                h_ = 3 + int(4 * abs(math.sin(x * 1.7)))
                for y in range(T - h_, T):
                    L.put(x + (1 if y < T - 3 and x % 2 else 0), y, grass[3] if y < T - 2 else grass[2], wrap=False)
        elif name == "deco_rock":
            for x in range(2, 14):
                for y in range(8, T):
                    if ((x - 8) / 6) ** 2 + ((y - 15) / 7) ** 2 <= 1:
                        l = (x - 8) * -0.6 + (y - 15) * -0.8
                        L.put(x, y, b["rock"][2] if l > 2.5 else b["rock"][1] if l > -1 else b["rock"][0], wrap=False)
            L.put(5, 11, grass[3], wrap=False)
            L.put(6, 10, grass[3], wrap=False)
    return L


def build(biome):
    b = BIOMES[biome]
    base = f"art/source/jungle/{biome}"
    seed = sum(map(ord, biome))
    sky(b, seed).json(f"{base}/sky.json", extra={"parallax": 0.1})
    far(b, seed + 1).json(f"{base}/far.json", extra={"parallax": 0.25})
    mid(b, seed + 2).json(f"{base}/mid.json", extra={"parallax": 0.5})
    fore(b, seed + 3).json(f"{base}/fore.json", extra={"parallax": 1.4})
    tiles = [tile(b, n, seed + i) for i, n in enumerate(TILE_NAMES)]
    tiles[0].json(f"{base}/tiles.json", name="tiles", frames=tiles, extra={"tile_names": TILE_NAMES, "tile_size": T})


if __name__ == "__main__":
    for bio in sys.argv[1:] or list(BIOMES):
        build(bio)
