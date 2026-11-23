# Builds the mini-game backgrounds (ART_BRIEF §9), portrait 225x487 each.
# Usage: python tools/build_scenes.py [word|block|brew|rune|forage ...]
#        python tools/render.py art/source/scenes/<scene>_bg.json --out art/out/scenes/<scene>_bg --scale 2
#
#   word    Word Rush: a rocky cliff path at dusk, all the action in the top half (the keyboard
#           covers the bottom). Skerbie guards on the left, enemies charge in from the right.
#   block   Block Party: a round stone arena in a moonlit clearing seen from high up, 4 faint hit
#           rings (up/down/left/right), the bottom third left calm and dark for the 4 thumb pads.
#   brew    Potion Brew: a close-up of his alchemy corner: a hearth for the cauldron, room in the
#           steam above it for the target number, and a shelf along the bottom for 6 ingredients.
#   rune    Rune Lock: an ancient stone seal door filling the screen, a recessed grid (up to 5x5
#           tiles of 36 px) in its middle, a socket for the source rune above and the seal below.
#   forage  Foraging: a misty forest clearing, an old twisted fruit tree whose canopy fills the top
#           (the foods fall from it) and a grassy floor along the bottom where he runs and catches.
# Like the tavern: every material has a 5-step ramp (dark -> lit) and a light pass shifts pixels up
# the ramp near light sources, Bayer-dithered only at the edges of the light. No hard outlines
# (backgrounds), colours from §3. Each JSON has "spots": where the game puts characters and props.
import json, math, os, random, sys

W, H = 225, 487
OUT = "art/source/scenes"
os.makedirs(OUT, exist_ok=True)
RAMP = {
    "rock":  ["#17151c", "#2a2036", "#3a2d4a", "#4a3a5c", "#a8643a"],
    "rockc": ["#17151c", "#23212b", "#2a2036", "#3a2d4a", "#4a3a5c"],   # cliff face in shadow
    "stone": ["#17151c", "#2a3448", "#3b4a63", "#4d5e7a", "#8a8494"],
    "slate": ["#17151c", "#23212b", "#2a3448", "#3b4a63", "#4d5e7a"],
    "grass": ["#17151c", "#2c4234", "#3e5a46", "#557a5c", "#a8945e"],
    "ngrass": ["#17151c", "#1f3d44", "#2c4234", "#3e5a46", "#557a5c"],  # moonlit grass
    "earth": ["#17151c", "#2a2036", "#3a2d4a", "#4a3a5c", "#7a5636"],
    "wood":  ["#17151c", "#3b2a22", "#7a5636", "#a8945e", "#ffd08a"],
    "dwood": ["#17151c", "#23212b", "#3b2a22", "#7a5636", "#a8945e"],
    "bark":  ["#17151c", "#23212b", "#3b2a22", "#7a5636", "#8b7a4a"],
    "leaf":  ["#17151c", "#1f3d44", "#2c4234", "#3e5a46", "#557a5c"],
    "iron":  ["#17151c", "#33303d", "#5a5e66", "#c9cfd6", "#c9cfd6"],
    "chalk": ["#2a2036", "#4a3a5c", "#8b7a4a", "#a8945e", "#bfae8c"],
    "mist":  ["#3a2d4a", "#4a3a5c", "#4d5e7a", "#8a8494", "#c9cfd6"],
    "rune":  ["#2a2036", "#3a2d4a", "#4a3a5c", "#6a2cc9", "#9b4dff"],    # carved channels, unlit (dusky)
    "moon":  ["#3b4a63", "#4d5e7a", "#9fc9f0", "#cfe9ff", "#f2f9ff"],
}
FIXED = {"f0": "#ffd08a", "f1": "#ffb35c", "f2": "#ff8a3d", "f3": "#c2410c", "pink": "#f2a0b0", "peach": "#ffc8a8",
         "amber": "#ffb35c", "star": "#cfe9ff", "star2": "#9fc9f0", "teal": "#2ec4b6", "tealhi": "#8ff0e6",
         "moss": "#557a5c", "moon0": "#f2f9ff", "moon1": "#cfe9ff", "moon2": "#9fc9f0"}
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def inside(poly, x, y):
    px, py, hit = x + .5, y + .5, False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[i - 1]
        if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


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


class Scene:
    def __init__(self, name):
        self.name = name
        self.mat = [[None] * W for _ in range(H)]
        self.fixed = {}
        self.lights = []          # (x, y, radius, strength)
        self.spots = {}
        self.sky = {}             # (x, y) -> colour for gradient skies (not lit)

    def put(self, x, y, m, s):
        x, y = int(x), int(y)
        if 0 <= x < W and 0 <= y < H:
            self.mat[y][x] = (m, max(0, min(4, s)))
            self.fixed.pop((x, y), None)
            self.sky.pop((x, y), None)

    def fix(self, x, y, key):
        x, y = int(x), int(y)
        if 0 <= x < W and 0 <= y < H:
            self.fixed[(x, y)] = key

    def poly(self, pts, m, s):
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        for y in range(max(0, int(min(ys))), min(H, int(max(ys)) + 1)):
            for x in range(max(0, int(min(xs))), min(W, int(max(xs)) + 1)):
                if inside(pts, x, y):
                    self.put(x, y, m, s(x, y) if callable(s) else s)

    def box(self, x0, y0, x1, y1, m, s, edge=True):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                e = s
                if edge and (y == y0 or x == x0):
                    e = s + 1
                elif edge and (y == y1 or x == x1):
                    e = s - 1
                self.put(x, y, m, e)

    def disc(self, cx, cy, rx, ry, m, s, shade=True):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                dx, dy = (x + .5 - cx) / rx, (y + .5 - cy) / ry
                if dx * dx + dy * dy <= 1:
                    lit = (dx * -0.6 + dy * -0.8)
                    self.put(x, y, m, s + ((1 if lit > 0.45 else -1 if lit < -0.5 else 0) if shade else 0))

    def ring(self, cx, cy, rx, ry, m, s, width=1, keep=1.0, seed=0):
        for a10 in range(0, 3600, 3):
            a = math.radians(a10 / 10)
            for d in range(width):
                x = int(round(cx + (rx - d) * math.cos(a)))
                y = int(round(cy + (ry - d * ry / rx) * math.sin(a)))
                if noise(x, y, 4, seed) < keep:
                    self.put(x, y, m, s)

    def branch(self, pts, w0, w1, m, base=2):
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
                        lit = ((x + .5 - cx) * -0.6 + (y + .5 - cy) * -0.8) / max(r, .5)
                        self.put(x, y, m, base + (1 if lit > 0.5 else -1 if lit < -0.45 else 0))

    def gradient(self, y0, y1, colours, x0=0, x1=W - 1):
        # A dithered vertical sky gradient through the listed colours.
        n = len(colours) - 1
        for y in range(y0, y1 + 1):
            t = (y - y0) / max(1, y1 - y0) * n
            i = min(n - 1, int(t))
            f = t - i
            for x in range(x0, x1 + 1):
                c = colours[i + 1] if f > (BAYER[y % 4][x % 4] + 0.5) / 16 else colours[i]
                self.sky[(x, y)] = c
                self.mat[y][x] = None

    def write(self):
        pal, inv, rows = {}, {}, []
        chars = iter("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&*+-=?@^_~")

        def code(col):
            if col not in inv:
                inv[col] = next(chars)
                pal[inv[col]] = col
            return inv[col]

        for y in range(H):
            line = []
            for x in range(W):
                if (x, y) in self.fixed:
                    line.append(code(FIXED[self.fixed[(x, y)]]))
                    continue
                cell = self.mat[y][x]
                if cell is None:
                    line.append(code(self.sky.get((x, y), "#17151c")))
                    continue
                m, s = cell
                v = 0.0
                for lx, ly, rad, k in self.lights:
                    d = math.hypot((x - lx) * 0.9, (y - ly) * 1.1)
                    v += k * max(0.0, 1 - d / rad) ** 1.6
                thr = (BAYER[y % 4][x % 4] + 0.5) / 16
                lift = int(v) + (1 if (v - int(v)) > 0.5 + (thr - 0.5) * 0.4 else 0)
                line.append(code(RAMP[m][max(0, min(4, s + lift))]))
            rows.append("".join(line))
        json.dump({"width": W, "height": H, "fps": 1, "palette": pal, "dye_zones": {}, "attach": {},
                   "spots": self.spots, "animations": {"bg": [rows]}}, open(f"{OUT}/{self.name}_bg.json", "w"))
        print("wrote", self.name, len(pal), "colours")


# ============================================================================ Word Rush
def word():
    sc = Scene("word")
    PATH = 206                                                    # the fighters' feet
    sc.gradient(0, 120, ["#2a2036", "#3a2d4a", "#4a3a5c", "#f2a0b0", "#ffb35c", "#ffd08a"])
    for y in range(80, 121):                                      # the low sun, half behind the peaks
        for x in range(150, 196):
            d = math.hypot(x - 172, (y - 104) * 1.1)
            if d < 13:
                sc.sky[(x, y)] = "#ffd08a" if d < 10 else "#ffc8a8"
    rnd = random.Random(3)
    for layer, (base, amp, m, s, seed) in enumerate(((112, 30, "rockc", 2, 1), (128, 26, "rockc", 1, 2))):
        for x in range(W):                                        # two ranges of jagged peaks
            n = noise(x, 0, 18 - layer * 5, seed) * amp + noise(x, 0, 5, seed + 9) * 6
            top = int(base - n)
            for y in range(top, 215):
                sc.put(x, y, m, s)
    for y in range(134, 160):                                     # mist pooled in the valley
        for x in range(W):
            if noise(x, y * 2, 16, 5) > 0.55 + (y - 134) * 0.01:
                sc.put(x, y, "mist", 1 if noise(x, y, 6, 7) > 0.5 else 0)
    # the near cliff: a rising wall of rock behind the path on the left, the path ledge, the drop below
    sc.poly([(0, 120), (18, 104), (34, 112), (52, 96), (70, 118), (84, 150), (90, PATH)] + [(0, PATH)],
            "rock", lambda x, y: 2 if noise(x, y, 4, 11) > 0.72 else 1)
    for x in range(W):                                            # the path: a lit top edge, then broken rock
        surf = PATH + int(noise(x, 0, 9, 13) * 3)
        for y in range(surf - 3, surf + 9):
            n = noise(x, y, 4, 14)
            s = 3 if y < surf - 1 else 2 if n > 0.7 else 1
            sc.put(x, y, "rock", s)
        for y in range(surf + 9, H):                              # the cliff face falls away into dark
            n = noise(x * 2.5, y * 0.5, 8, 15)                    # vertical strata, fading into the dark
            depth = (y - surf) / 110
            s = max(0, int((2 if n > 0.62 else 1) - depth))
            sc.put(x, y, "rockc", s)
    for cx, cy, r in ((26, PATH - 6, 6), (128, PATH - 4, 4), (196, PATH - 5, 5), (160, PATH - 3, 3)):
        sc.disc(cx, cy, r * 1.4, r, "rock", 2)                    # boulders along the path
    sc.branch([(70, PATH - 4), (68, 170), (74, 150), (66, 132)], 4, 1.5, "bark")      # a dead tree
    sc.branch([(69, 158), (58, 146), (52, 148)], 2, 1, "bark")
    sc.branch([(72, 146), (82, 136)], 2, 1, "bark")
    for x in range(W):                                            # rim light from the sunset on the path's top edge
        for y in range(PATH - 6, PATH + 2):
            c = sc.mat[y][x]
            if c and c[0] == "rock" and (sc.mat[y - 1][x] is None or sc.mat[y - 1][x][0] == "mist"):
                sc.put(x, y, "rock", 4 if x > 100 else 3)
    for y in range(0, 60):                                        # a few early stars
        for x in range(W):
            if random.Random(x * 3 + y * 977).random() < 0.004:
                sc.fix(x, y, "star")
    sc.lights = [(172, 104, 150, 0.9)]
    sc.spots = {"skerbie": [44, PATH], "enemy_enter": [240, PATH], "knockback_line": [82, PATH],
                "word_sign": [150, 152], "play_area_bottom": 243}
    sc.write()


# ============================================================================ Block Party
def block():
    sc = Scene("block")
    CX, CY, R = 112, 196, 92
    for y in range(H):                                            # the clearing: moonlit grass
        for x in range(W):
            n = noise(x, y, 3, 21)
            sc.put(x, y, "ngrass", 2 if n > 0.74 else 1)
    for (bx, by, r) in ((0, 0, 50), (225, 10, 46), (0, 300, 40), (225, 290, 44), (40, -10, 30), (190, -12, 30),
                        (-10, 140, 30), (235, 150, 30)):          # tree crowns looming at the edges
        for y in range(int(by - r) - 2, int(by + r) + 3):
            for x in range(int(bx - r) - 2, int(bx + r) + 3):
                d = math.hypot(x - bx, y - by) + (noise(x, y, 5, 22) - 0.5) * 12
                if d < r:
                    sc.put(x, y, "leaf", 2 if d < r * 0.6 and noise(x, y, 3, 23) > 0.7 else 1 if d < r * 0.88 else 0)
    # the arena: rings of flagstones, a raised central dais
    for y in range(CY - R - 1, CY + R + 2):
        for x in range(CX - R - 1, CX + R + 2):
            d = math.hypot(x - CX, y - CY)
            if d <= R:
                ring = int(d // 14)
                ang = math.degrees(math.atan2(y - CY, x - CX)) % 360
                seg = int(ang // (360 / (6 + ring * 4)))
                joint = abs(d - ring * 14) < 0.8 or abs((ang % (360 / (6 + ring * 4)))) < 360 / (6 + ring * 4) * 0.05 * (6 - ring * 0.5)
                s = 0 if joint else 2 if random.Random(ring * 97 + seg).random() < 0.6 else 1
                sc.put(x, y, "stone", s)
    sc.ring(CX, CY, R, R, "stone", 3, width=2)                    # a kerb of lighter stone round the edge
    sc.ring(CX, CY, R + 2, R + 2, "slate", 0, width=2)
    sc.disc(CX, CY, 17, 17, "stone", 2)                           # the dais
    sc.ring(CX, CY, 17, 17, "stone", 3)
    for k in range(8):                                            # rune marks round the dais
        a = math.radians(k * 45 + 22)
        sc.put(CX + 13 * math.cos(a), CY + 13 * math.sin(a), "rune", 2)
    # 4 faint hit rings, one per direction
    HIT = 54
    hits = {"up": [CX, CY - HIT], "down": [CX, CY + HIT], "left": [CX - HIT, CY], "right": [CX + HIT, CY]}
    for hx, hy in hits.values():
        sc.ring(hx, hy, 12, 12, "chalk", 1, width=2, keep=0.8, seed=hx + hy)
    for (bx, by) in ((22, 120), (204, 118), (30, 280), (196, 276), (112, 86)):         # moss on the outer stones
        for y in range(by - 6, by + 7):
            for x in range(bx - 8, bx + 9):
                if noise(x, y, 3, 25) > 0.6 and sc.mat[y][x] and sc.mat[y][x][0] == "stone":
                    sc.put(x, y, "ngrass", 3)
    for y in range(300, H):                                       # the bottom third settles into calm dark grass
        for x in range(W):
            c = sc.mat[y][x]
            if c and c[0] == "ngrass":
                sc.put(x, y, "ngrass", max(0, c[1] - (1 if y > 340 else 0)))
    for k in range(40):                                           # fireflies / moonlit glints in the grass
        x, y = random.Random(k).randint(5, 220), random.Random(k + 99).randint(300, 480)
        if random.Random(k * 7).random() < 0.5:
            sc.fix(x, y, "star2")
    sc.lights = [(70, 120, 210, 1.3), (CX, CY, 70, 0.5)]           # moonlight from the upper left
    sc.spots = {"skerbie": [CX, CY + 6], "centre": [CX, CY], "hit_rings": hits, "hit_ring_radius": 12,
                "enemy_enter": {"up": [CX, -20], "down": [CX, 330], "left": [-20, CY], "right": [245, CY]},
                "pads": {"up": [112, 360], "left": [62, 410], "right": [162, 410], "down": [112, 460]},
                "beat_pulse_centre": [CX, CY]}
    sc.write()


# ============================================================================ Potion Brew
def brew():
    sc = Scene("brew")
    for y in range(H):                                            # back wall: rough stone blocks
        course = y // 12
        for x in range(W):
            off = (course % 2) * 14
            joint = y % 12 == 0 or (x + off) % 28 == 0
            blk = random.Random(course * 31 + (x + off) // 28).random()
            sc.put(x, y, "stone", 0 if joint else 1 if blk < 0.65 else 2)
    # a round window high on the wall, night sky with a sliver of moon
    WX, WY, WR = 168, 62, 26
    for y in range(WY - WR, WY + WR + 1):
        for x in range(WX - WR, WX + WR + 1):
            d = math.hypot(x - WX, y - WY)
            if d < WR - 3:
                sc.sky[(x, y)] = "#2a3448" if y < WY else "#3b4a63"
                sc.mat[y][x] = None
            elif d < WR:
                sc.put(x, y, "dwood", 3 if (x < WX and y < WY) else 2)
    for x in range(WX - WR + 3, WX + WR - 2):                     # window cross bars
        sc.put(x, WY, "dwood", 2)
    for y in range(WY - WR + 3, WY + WR - 2):
        sc.put(WX, y, "dwood", 2)
    for dx, dy in ((-12, -10), (6, -16), (14, 8), (-8, 12)):
        sc.fix(WX + dx, WY + dy, "star")
    for x in range(WX + 6, WX + 13):                              # crescent moon
        for y in range(WY - 14, WY - 6):
            if math.hypot(x - WX - 9, y - WY + 10) < 4 and math.hypot(x - WX - 11, y - WY + 11) >= 3.5:
                sc.fix(x, y, "moon1")
    # hanging herbs and a ladle rack along the top
    sc.box(0, 18, 130, 21, "wood", 2)
    for i, x in enumerate(range(10, 128, 14)):
        sc.put(x, 22, "bark", 2)
        if i % 3 == 1:                                            # a ladle / spoon
            sc.branch([(x, 22), (x, 44)], 2, 2, "iron", 2)
            sc.disc(x, 47, 3, 2.4, "iron", 2)
        else:
            for k in range(10 + i % 3 * 2):
                w = 1 + k // 4
                for d in range(-w, w + 1):
                    if (i + k + d) % 3:
                        sc.fix(x + d, 23 + k, "moss")
                    else:
                        sc.put(x + d, 23 + k, "bark", 3)
    # the hearth: an arched stone fire-pit the cauldron hangs over
    HY = 360                                                      # hearth floor
    sc.poly([(28, HY), (36, 250), (60, 226), (112, 214), (164, 226), (188, 250), (196, HY)], "slate",
            lambda x, y: 1 if noise(x, y, 3, 31) > 0.78 else 0)
    for y in range(226, HY):                                      # arch of dressed stone round the pit
        for x in range(28, 197):
            d = math.hypot((x - 112) / 84, (y - HY) / 140)
            if 0.9 < d < 1.02:
                sc.put(x, y, "stone", 3 if x < 112 else 2)
    for x in range(52, 173):                                      # glowing embers and coals in the pit
        for y in range(HY - 10, HY):
            n = noise(x, y, 3, 33)
            if n > 0.45:
                sc.fix(x, y, "f2" if n > 0.75 else "f3")
            elif n > 0.3:
                sc.put(x, y, "earth", 1)
    for k in range(9):                                            # small flames licking up
        x = 60 + k * 13
        hgt = 6 + (k * 7) % 6
        for y in range(HY - 10 - hgt, HY - 10):
            t = (HY - 10 - y) / hgt
            for dx in range(-2, 3):
                if abs(dx) < 2.5 * (1 - t):
                    sc.fix(x + dx, y, "f0" if t > 0.6 and dx == 0 else "f1" if t > 0.3 else "f2")
    sc.box(20, HY, 204, HY + 6, "stone", 2)                       # hearth stone lip
    # the shelf of ingredients along the bottom, on iron brackets
    SY = 446
    sc.box(4, SY, 220, SY + 7, "wood", 2)
    for x in range(4, 221):
        sc.put(x, SY + 8, "dwood", 0)
    for bx in (20, 112, 204):
        sc.branch([(bx, SY + 8), (bx, SY + 22), (bx - 8, SY + 9)], 2, 2, "iron", 2)
    for x, kind in ((14, "candle"), (212, "candle")):             # candles at the shelf ends
        sc.box(x - 2, SY - 10, x + 1, SY - 1, "chalk", 3, edge=False)
        sc.fix(x - 1, SY - 11, "f0")
        sc.fix(x, SY - 12, "f1")
    sc.lights = [(112, HY - 20, 150, 2.0), (14, SY - 12, 50, 0.9), (212, SY - 12, 50, 0.9), (WX, WY, 40, 0.4)]
    sc.spots = {"cauldron": [112, HY - 4], "target_number": [112, 150], "shelf_top": SY,
                "ingredients": [[22 + i * 36, SY] for i in range(6)], "plume_origin": [112, 270]}
    sc.write()


# ============================================================================ Rune Lock
def rune():
    sc = Scene("rune")
    for y in range(H):                                            # the cave around the door
        for x in range(W):
            n = noise(x, y, 11, 41)
            sc.put(x, y, "rockc", 2 if n > 0.75 else 1 if n > 0.3 else 0)
    # the door slab: arched top, a carved border, a recessed grid, sockets for source and seal
    DX0, DX1, DTOP, DBOT = 8, 216, 40, 470
    def door(x, y):
        if y > DTOP + 104:
            return DX0 <= x <= DX1
        return math.hypot((x - 112) / 104, (y - DTOP - 104) / 104) <= 1
    for y in range(DTOP, DBOT + 1):
        for x in range(DX0, DX1 + 1):
            if door(x, y):
                n = noise(x, y, 9, 43)
                sc.put(x, y, "slate", 2 if n > 0.72 else 1)
    for y in range(DTOP, DBOT + 1):                               # the carved border band
        for x in range(DX0, DX1 + 1):
            if door(x, y) and not (door(x - 8, y) and door(x + 8, y) and door(x, y - 8) and y < DBOT - 8):
                sc.put(x, y, "stone", 3 if (x < 112 and y < 250) else 2)
    for k in range(64):                                           # rune glyphs carved round the border
        if k < 24:
            a = math.radians(180 + k * 7.5)
            gx, gy = 112 + 100 * math.cos(a), DTOP + 104 + 100 * math.sin(a)
        elif k < 44:
            gx, gy = DX0 + 4, DTOP + 108 + (k - 24) * 16
        else:
            gx, gy = DX1 - 4, DTOP + 108 + (k - 44) * 16
        shape = random.Random(k).choice((((0, -1), (0, 0), (0, 1)), ((-1, -1), (0, 0), (1, 1)), ((-1, 0), (0, 0), (1, 0), (0, 1)),
                                         ((0, -1), (-1, 0), (1, 0), (0, 1))))
        for dx, dy in shape:
            sc.put(gx + dx, gy + dy, "rune", 2)
    # the recessed grid well (5x5 tiles of 36 px)
    GX, GY, TS = 22, 152, 36
    sc.box(GX - 4, GY - 4, GX + 5 * TS + 3, GY + 5 * TS + 3, "slate", 0, edge=False)
    for i in range(6):                                            # faint grid lines in the well floor
        for t in range(5 * TS):
            sc.put(GX + i * TS - (1 if i == 5 else 0), GY + t, "slate", 1)
            sc.put(GX + t, GY + i * TS - (1 if i == 5 else 0), "slate", 1)
    for x in range(GX - 4, GX + 5 * TS + 4):                      # lit top-left lip, shadowed bottom-right
        sc.put(x, GY - 5, "stone", 3)
        sc.put(x, GY + 5 * TS + 4, "slate", 0)
    for y in range(GY - 4, GY + 5 * TS + 4):
        sc.put(GX - 5, y, "stone", 3)
        sc.put(GX + 5 * TS + 4, y, "slate", 0)
    # the source rune socket above the grid, the seal socket below, a sun-and-eye motif in the arch
    for (sx, sy, r) in ((112, 120, 15), (112, 372, 20)):
        sc.disc(sx, sy, r, r, "slate", 0, shade=False)
        sc.ring(sx, sy, r + 2, r + 2, "stone", 3, width=2)
    sc.ring(112, 78, 22, 22, "rune", 2, width=1)
    for k in range(12):
        a = math.radians(k * 30)
        for t in range(24, 30):
            sc.put(112 + t * math.cos(a), 78 + t * math.sin(a), "rune", 2)
    sc.disc(112, 78, 9, 6, "rune", 1, shade=False)
    sc.disc(112, 78, 3.5, 3.5, "rune", 3, shade=False)
    for y in range(DTOP, DBOT):                                   # cracks and moss in the old stone
        for x in range(DX0, DX1):
            if door(x, y) and y > 420 and noise(x, y, 4, 48) > 0.7:
                sc.put(x, y, "grass", 2)
    for pts in (((40, 60), (48, 74), (44, 88), (52, 100)), ((176, 410), (168, 424), (172, 440)), ((30, 400), (40, 412))):
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):                  # a few long cracks in the old stone
            for t in range(13):
                sc.put(ax + (bx - ax) * t / 12, ay + (by - ay) * t / 12, "slate", 0)
    for tx in (0, 210):                                           # wall torches either side, in the cave rock
        sc.box(tx + 3, 252, tx + 11, 256, "iron", 2)
        sc.branch([(tx + 7, 256), (tx + 7, 270)], 3, 2, "dwood", 2)
        for y in range(238, 252):
            t = (252 - y) / 14
            for dx in range(-3, 4):
                if abs(dx) < 3.5 * (1 - t):
                    sc.fix(tx + 7 + dx, y, "f0" if t > 0.5 and dx == 0 else "f1" if t > 0.25 else "f2")
    sc.lights = [(7, 246, 110, 1.5), (217, 246, 110, 1.5), (112, 300, 160, 0.4)]
    sc.spots = {"grid_origin": [GX, GY], "tile_size": TS, "grid_max": 5, "source_rune": [112, 120],
                "seal_glyph": [112, 372], "hint_button": [196, 30]}
    sc.write()


# ============================================================================ Foraging
def forage():
    sc = Scene("forage")
    GROUND = 438
    sc.gradient(0, 300, ["#2a3448", "#3b4a63", "#4d5e7a", "#8a8494"])
    rnd = random.Random(5)
    # two rows of distant trees, softened by mist: straight trunks under round, layered crowns
    for layer, (base, trunk_m, crown_m, shade, count, size) in enumerate(((330, "mist", "mist", 1, 9, 22), (370, "leaf", "leaf", 1, 7, 28))):
        for k in range(count):
            tx = int((k + 0.5) * W / count + rnd.uniform(-8, 8))
            top = base - rnd.randint(size * 3, size * 4)
            for y in range(top + size, GROUND + 2):
                for x in range(tx - 2 - layer, tx + 3 + layer):
                    sc.put(x, y, trunk_m, shade - (1 if x > tx + layer else 0))
            for (dx, dy, r) in ((0, 0, size), (-size * 0.6, size * 0.7, size * 0.8), (size * 0.6, size * 0.6, size * 0.8)):
                cx, cy = tx + dx, top + size + dy
                for y in range(int(cy - r), int(cy + r) + 1):
                    for x in range(int(cx - r), int(cx + r) + 1):
                        if math.hypot(x - cx, (y - cy) * 1.2) < r:
                            lit = ((x - cx) * -0.6 + (y - cy) * -0.8) / r
                            sc.put(x, y, crown_m, shade + (1 if lit > 0.45 else 0))
        for y in range(base - 10, base + 40):                    # a soft band of mist in front of each row
            for x in range(W):
                t = 1 - abs(y - base - 15) / 25
                if noise(x, y * 3, 24, 60 + layer) * t > 0.32:
                    sc.put(x, y, "mist", 2)
    for y in range(300, GROUND):                                  # the far floor, misty
        for x in range(W):
            if sc.mat[y][x] is None:
                sc.put(x, y, "mist", 1)
    for y in range(GROUND, H):                                    # the clearing floor: grass and leaf litter
        for x in range(W):
            n = noise(x, y, 3, 57)
            sc.put(x, y, "grass", 3 if y < GROUND + 2 else 2 if n > 0.7 else 1)
    for x in range(0, W, 3):                                      # grass tufts along the edge
        h = 2 + int(noise(x, 0, 3, 58) * 4)
        for y in range(GROUND - h, GROUND):
            sc.put(x + (y % 2), y, "grass", 3)
    # the old twisted fruit tree: a thick gnarled trunk that twists up the middle, roots, spreading boughs
    trunk = [(36, GROUND + 4), (30, 410), (42, 380), (38, 350), (56, 320), (78, 292), (104, 264)]
    for pts, w0, w1 in (([(36, GROUND), (8, GROUND + 6)], 12, 4), ([(40, GROUND), (72, GROUND + 6)], 12, 4),
                        ([(34, GROUND), (24, GROUND + 8)], 8, 3)):
        sc.branch(pts, w0, w1, "bark", 2)
    sc.branch(trunk, 40, 20, "bark", 2)
    for k in range(1, 6):                                         # twisting grooves up the trunk
        (ax, ay), (bx, by) = trunk[k], trunk[k + 1]
        for t in range(12):
            x = ax + (bx - ax) * t / 11 + (t - 6) * 0.8
            sc.put(x, ay + (by - ay) * t / 11, "bark", 1)
    for pts, w0, w1 in (([(104, 264), (70, 236), (36, 214)], 16, 6), ([(104, 264), (150, 236), (190, 220)], 16, 6),
                        ([(100, 268), (114, 220), (108, 180)], 14, 6), ([(70, 236), (58, 200)], 8, 3),
                        ([(150, 236), (168, 200)], 8, 3)):
        sc.branch(pts, w0, w1, "bark", 2)
    for (cx, cy, r) in ((112, 128, 46), (58, 162, 40), (168, 158, 40), (24, 196, 26), (204, 192, 26), (86, 96, 34),
                        (142, 92, 34), (112, 190, 32)):            # the canopy: separate clumps, each lit on its own
        for y in range(int(cy - r) - 3, int(cy + r) + 4):
            for x in range(int(cx - r) - 3, int(cx + r) + 4):
                d = math.hypot(x - cx, (y - cy) * 1.15) / r + (noise(x, y, 4, 61) - 0.5) * 0.18
                if d < 1:
                    lit = ((x - cx) * -0.6 + (y - cy) * -0.8) / r
                    speck = noise(x, y, 2.2, 63)
                    base = 3 if lit > 0.35 else 2 if lit > -0.45 else 1
                    sc.put(x, y, "leaf", base + (1 if speck > 0.8 and base < 3 else -1 if speck < 0.18 else 0))
                elif d < 1.06 and 0 <= x < W and 0 <= y < H and sc.mat[y][x] and sc.mat[y][x][0] == "leaf":
                    sc.put(x, y, "leaf", 0)                         # a dark gap where clumps overlap
    for k in range(80):                                           # fruit and blossoms dotted through the leaves
        x, y = random.Random(k * 13).randint(8, 216), random.Random(k * 29).randint(60, 222)
        c = sc.mat[y][x]
        if c and c[0] == "leaf" and c[1] >= 2:
            key = random.Random(k).choice(("pink", "peach", "amber"))
            sc.fix(x, y, key)
            sc.fix(x + 1, y, key)
            if k % 2:
                sc.fix(x, y + 1, key)
    for y in range(GROUND - 22, GROUND + 3):                      # low mist drifting over the clearing floor
        for x in range(W):
            t = 1 - abs(y - GROUND + 10) / 14
            if noise(x, y * 3, 22, 65) * t > 0.38 and sc.mat[y][x] and sc.mat[y][x][0] != "bark":
                sc.put(x, y, "mist", 2)
    sc.lights = [(160, 30, 170, 0.8)]
    sc.spots = {"skerbie_run_y": GROUND + 8, "run_x_min": 18, "run_x_max": 207, "drop_zone": [20, 90, 205, 210],
                "ground": GROUND + 8}
    sc.write()


SCENES = {"word": word, "block": block, "brew": brew, "rune": rune, "forage": forage}
if __name__ == "__main__":
    for n in sys.argv[1:] or list(SCENES):
        SCENES[n]()
