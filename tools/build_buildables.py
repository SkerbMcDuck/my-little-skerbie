# Builds the home buildables (ART_BRIEF §6.1): 12 items x 3 den tiers (Burrow, Hideout,
# Lair), plus the shared scaffold and damage kit.
# Usage: python tools/build_buildables.py
#        then render each art/source/home/buildables/<item>.json with tools/render.py
#
# Each item JSON has one animation per tier ("burrow", "hideout", "lair"; the hearth's fire
# has 4 frames, the decor's flame flickers over 3). "anchor" is the pixel that sits on the
# item's spot in the den JSON ("spots"): bottom-centre for things on the floor or ground,
# centre for things on the wall. Props are interactive, so like characters they get a dark
# outline and flat faceted shading lit from the top-left; all colours are from the §3 palette.
import json, math, os, random

OUT = "art/source/home/buildables"
os.makedirs(OUT, exist_ok=True)
OUTLINE = "#0f0d14"
R = {  # material ramps: highlight, base, shadow, deep
    "wood":   ["#a8945e", "#7a5636", "#3b2a22", "#17151c"],
    "dark":   ["#7a5636", "#3b2a22", "#23212b", "#17151c"],
    "stone":  ["#4d5e7a", "#3b4a63", "#2a3448", "#17151c"],
    "iron":   ["#c9cfd6", "#5a5e66", "#33303d", "#17151c"],
    "moss":   ["#557a5c", "#3e5a46", "#2c4234", "#17151c"],
    "fur":    ["#8a8494", "#615b6b", "#433e4c", "#2c2833"],
    "cloth":  ["#4a3a5c", "#3a2d4a", "#2a2036", "#17151c"],
    "bone":   ["#bfae8c", "#a8945e", "#8b7a4a", "#3b2a22"],
    "parch":  ["#bfae8c", "#bfae8c", "#a8945e", "#8b7a4a"],
    "soil":   ["#4a3a5c", "#3a2d4a", "#2a2036", "#17151c"],
    "slate":  ["#3b4a63", "#2a3448", "#23212b", "#17151c"],
    "teal":   ["#8ff0e6", "#2ec4b6", "#178f86", "#1f3d44"],
    "warm":   ["#ffd08a", "#ffb35c", "#ff8a3d", "#c2410c"],
    "fire":   ["#ffe08a", "#ffb347", "#ff7a1a", "#c2410c"],
    "pink":   ["#ffc8a8", "#f2a0b0", "#f2a0b0", "#4a3a5c"],
    "earth":  ["#a8945e", "#8b7a4a", "#5f7a3a", "#2c4234"],
}
LX, LY = -0.6, -0.8
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def inside(poly, x, y):
    px, py, hit = x + .5, y + .5, False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[i - 1]
        if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.g, self.part, self.ramp = {}, {}, {}
        self.n = 0

    def _paint(self, pts, ramp, flat=None):
        if not pts:
            return
        self.n += 1
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        cx, cy = (min(xs) + max(xs) + 1) / 2, (min(ys) + max(ys) + 1) / 2
        hw, hh = max(1, (max(xs) - min(xs) + 1) / 2), max(1, (max(ys) - min(ys) + 1) / 2)
        for (x, y) in pts:
            if 0 <= x < self.w and 0 <= y < self.h:
                lit = (x + .5 - cx) / hw * LX + (y + .5 - cy) / hh * LY
                t = flat if flat is not None else 0 if lit > 0.5 else 1 if lit > -0.15 else 2 if lit > -0.55 else 3
                self.g[(x, y)], self.part[(x, y)], self.ramp[(x, y)] = R[ramp][t], self.n, ramp

    def poly(self, pts, ramp, flat=None):
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        cells = [(x, y) for y in range(int(min(ys)) - 1, int(max(ys)) + 2)
                 for x in range(int(min(xs)) - 1, int(max(xs)) + 2) if inside(pts, x, y)]
        self._paint(cells, ramp, flat)

    def box(self, x0, y0, x1, y1, ramp, flat=None):
        self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], ramp, flat)

    def blob(self, cx, cy, rx, ry, ramp, flat=None):
        cells = [(x, y) for y in range(int(cy - ry) - 1, int(cy + ry) + 2)
                 for x in range(int(cx - rx) - 1, int(cx + rx) + 2)
                 if ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1]
        self._paint(cells, ramp, flat)

    def stick(self, a, b, w0, w1, ramp, flat=None):
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln, dx / ln
        self.poly([(a[0] + nx * w0 / 2, a[1] + ny * w0 / 2), (b[0] + nx * w1 / 2, b[1] + ny * w1 / 2),
                   (b[0] - nx * w1 / 2, b[1] - ny * w1 / 2), (a[0] - nx * w0 / 2, a[1] - ny * w0 / 2)], ramp, flat)

    def px(self, x, y, colour):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.g[(x, y)] = colour

    def finish(self):
        # A deep seam where a later part sits on an earlier one, then the outline.
        g = dict(self.g)
        for p, k in self.part.items():
            for dx, dy in N4:
                q = (p[0] + dx, p[1] + dy)
                if q in self.part and self.part[q] < k and self.ramp[q] != self.ramp[p]:
                    g[p] = R[self.ramp[p]][3]
                    break
        for (x, y) in self.g:
            if any((x + dx, y + dy) not in self.g for dx, dy in N4):
                g[(x, y)] = OUTLINE
        return g


def to_json(name, w, h, anchor, tiers):
    # Turn hex-colour frames into palette characters.
    colours = sorted({c for frames in tiers.values() for f in frames for c in f.values()})
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    pal = {chars[i]: c for i, c in enumerate(colours)}
    inv = {c: k for k, c in pal.items()}
    anims = {t: [["".join(inv[f[(x, y)]] if (x, y) in f else "." for x in range(w)) for y in range(h)]
                 for f in frames] for t, frames in tiers.items()}
    json.dump({"width": w, "height": h, "fps": 8, "palette": pal, "dye_zones": {}, "attach": {},
               "anchor": anchor, "animations": anims}, open(f"{OUT}/{name}.json", "w"))


ITEMS = {}


def item(name, w, h, anchor, frames=1):
    def wrap(fn):
        ITEMS[name] = (w, h, anchor, frames, fn)
        return fn
    return wrap


def eyes(c, x, y):  # two dark sockets on a skull
    c.px(x, y, "#17151c")
    c.px(x + 3, y, "#17151c")


def flames(c, cx, base, width, f, scale=1.0):
    # Layered flame tongues whose heights shift each frame: deep orange outside, gold core.
    rnd = random.Random(f * 13 + int(cx))
    for k, dx in enumerate(range(-width // 2, width // 2 + 1, 3)):
        hgt = (6 + 4 * math.sin(f * 1.7 + k * 2.1) + rnd.random() * 2) * scale
        x = cx + dx
        c.poly([(x - 2, base), (x + 2, base), (x + 0.5, base - hgt)], "fire", flat=2)
        c.poly([(x - 1, base), (x + 1, base), (x + 0.3, base - hgt * 0.6)], "fire", flat=1)
    c.poly([(cx - width / 2 + 1, base), (cx + width / 2 - 1, base), (cx, base - 2.5 * scale)], "fire", flat=0)


# ---------------- 1. Bed: leaf pile -> root hammock -> fur-draped stone slab with skull headboard
@item("bed", 48, 24, [24, 23])
def bed(c, tier, f):
    if tier == "burrow":
        c.blob(24, 19, 21, 6, "moss")
        for x, y in ((10, 14), (17, 12), (25, 11), (33, 12), (39, 15), (21, 15), (30, 15)):
            c.blob(x, y, 4, 2.2, "earth" if (x // 7) % 2 else "moss")
    elif tier == "hideout":
        c.stick((5, 23), (6, 3), 4, 3, "wood")
        c.stick((43, 23), (42, 3), 4, 3, "wood")
        c.stick((6, 5), (11, 11), 1.4, 1.4, "parch")
        c.stick((42, 5), (37, 11), 1.4, 1.4, "parch")
        c.poly([(9, 10), (39, 10), (36, 16), (24, 19), (12, 16)], "cloth")
        c.blob(14, 11, 4, 2, "parch")                                  # a rolled pillow
    else:
        c.box(6, 15, 46, 23, "stone")
        c.poly([(8, 13), (42, 13), (44, 18), (40, 20), (32, 18), (22, 20), (12, 18), (7, 17)], "fur")
        c.box(1, 5, 7, 23, "stone")                                     # headboard post
        c.blob(4, 6, 4.5, 4.5, "bone")                                  # skull on top
        eyes(c, 2, 6)


# ---------------- 2. Pantry: wall hole with berries -> plank shelves with jars and herbs -> iron-banded larder
@item("pantry", 36, 40, [18, 20])
def pantry(c, tier, f):
    if tier == "burrow":
        c.blob(18, 22, 14, 12, "soil", flat=3)
        c.blob(18, 31, 10, 3, "soil", flat=2)                           # the hole's floor
        for x in (12, 16, 20, 23):
            c.blob(x, 30, 2.2, 2, "pink")
        c.blob(26, 29, 3, 1.6, "moss")                                  # a leaf
    elif tier == "hideout":
        for y in (16, 31):
            c.box(1, y, 35, y + 2, "wood")
            c.box(2, y + 2, 4, y + 6, "dark")
            c.box(32, y + 2, 34, y + 6, "dark")
        for x, mat in ((4, "teal"), (11, "parch"), (26, "teal")):
            c.box(x, 9, x + 5, 16, mat)
            c.box(x, 8, x + 5, 9, "wood")
        for x, mat in ((6, "parch"), (14, "teal"), (22, "parch")):
            c.box(x, 24, x + 5, 31, mat)
            c.box(x, 23, x + 5, 24, "wood")
        c.stick((20, 18), (20, 22), 1, 1, "wood")
        c.blob(20, 23, 2.4, 2.6, "moss")                                # hanging herbs
    else:
        c.box(3, 4, 33, 38, "dark")
        c.box(5, 6, 17, 36, "wood")
        c.box(19, 6, 31, 36, "wood")
        for y in (12, 29):
            c.box(3, y, 33, y + 2, "iron")
        c.px(16, 21, "#c9cfd6")
        c.px(20, 21, "#c9cfd6")
        for x in (10, 26):                                              # smoked meats on hooks
            c.stick((x, 1), (x, 6), 1, 1, "iron")
            c.blob(x, 9, 3, 4, "wood")


# ---------------- 3. Workbench: flat rock with stick and stones -> pegged bench with tools -> anvil and forge
@item("workbench", 38, 28, [19, 27])
def workbench(c, tier, f):
    if tier == "burrow":
        c.blob(19, 22, 17, 6, "stone")
        c.stick((8, 15), (24, 17), 2, 2, "wood")
        c.blob(28, 16, 3, 2.4, "stone")
        c.blob(32, 17, 2.2, 1.8, "stone")
    elif tier == "hideout":
        c.box(1, 11, 37, 14, "wood")
        c.box(4, 14, 7, 27, "wood")
        c.box(31, 14, 34, 27, "wood")
        c.box(7, 21, 31, 23, "wood")
        c.stick((12, 10), (12, 4), 1.6, 1.6, "wood")                   # a hammer
        c.box(9, 2, 16, 5, "iron")
        c.stick((22, 10), (28, 8), 1.6, 1.2, "iron")                   # a chisel
        for x in (3, 34):
            c.px(x, 12, "#a8945e")                                      # pegs
    else:
        c.box(0, 6, 12, 27, "stone")                                    # forge corner
        c.box(3, 15, 10, 24, "dark", flat=3)
        flames(c, 6.5, 24, 6, f, 0.7)
        c.poly([(14, 11), (32, 11), (37, 13), (32, 15), (28, 15), (27, 20), (30, 26), (17, 26), (20, 20),
                (19, 15), (14, 15)], "iron")                            # the anvil


# ---------------- 4. Chest: hollow log -> wooden trunk -> iron-bound chest with a rune lock
@item("chest", 26, 20, [13, 19])
def chest(c, tier, f):
    if tier == "burrow":
        c.blob(12, 13, 11, 6, "wood")
        c.blob(22, 13, 3.4, 5.4, "wood", flat=0)
        c.blob(22, 13, 2, 3.6, "dark", flat=3)                          # the hollow end
        for x in (5, 10, 15):
            c.stick((x, 9), (x + 2, 17), 0.8, 0.8, "dark")
    elif tier == "hideout":
        c.box(2, 8, 24, 19, "wood")
        c.box(1, 4, 25, 8, "wood")
        for x in (6, 18):
            c.box(x, 4, x + 2, 19, "dark")
        c.box(12, 7, 14, 10, "iron")
    else:
        c.box(2, 8, 24, 19, "dark")
        c.poly([(1, 8), (3, 3), (23, 3), (25, 8)], "dark")
        c.box(2, 8, 24, 9, "iron")
        for x in (5, 19):
            c.box(x, 3, x + 2, 19, "iron")
        c.box(10, 9, 16, 15, "iron")                                    # rune lock plate
        for p in ((13, 10), (12, 11), (14, 11), (13, 12), (13, 13)):
            c.px(*p, "#ffb35c")


# ---------------- 5. Walls & traps (in front of the door; a gap is left for the door):
#                   sharpened sticks -> palisade and snares -> spiked iron gates and rune wards
@item("walls_traps", 52, 26, [26, 25])
def walls(c, tier, f):
    left, right = (2, 6, 10, 14), (37, 41, 45, 49)
    if tier == "burrow":
        for x in left:
            c.stick((x + 1, 25), (x - 2, 9 + (x % 3)), 2.6, 0.6, "wood")
        for x in right:
            c.stick((x, 25), (x + 3, 9 + (x % 3)), 2.6, 0.6, "wood")
    elif tier == "hideout":
        for x in list(range(1, 17, 4)) + list(range(36, 52, 4)):
            c.box(x, 8, x + 3, 25, "wood")
            c.poly([(x, 8), (x + 3, 8), (x + 1.5, 4)], "wood")
        c.stick((1, 14), (17, 14), 1.4, 1.4, "parch")                  # lashing
        c.stick((36, 14), (52, 14), 1.4, 1.4, "parch")
        c.blob(26, 23, 3, 1.4, "parch")                                 # a snare loop on the path
        c.blob(26, 23, 1.6, 0.6, "dark", flat=3)
    else:
        for x0 in (1, 35):
            c.box(x0, 6, x0 + 16, 25, "iron")
            c.box(x0 + 2, 9, x0 + 14, 23, "dark", flat=3)
            for x in range(x0 + 3, x0 + 14, 3):
                c.box(x, 8, x + 1, 24, "iron")
                c.poly([(x - 0.5, 6), (x + 1.5, 6), (x + 0.5, 2)], "iron")
            c.px(x0 + 8, 15, "#ffb35c")                                 # rune wards
            c.px(x0 + 8, 16, "#ff8a3d")
            c.px(x0 + 7, 16, "#ffb35c")
            c.px(x0 + 9, 16, "#ffb35c")


# ---------------- 6. Training gear: a lifting rock -> dummy and weights -> full rack with an enchanted dummy
@item("training", 32, 36, [16, 35])
def training(c, tier, f):
    def dummy(body):
        c.stick((12, 35), (12, 10), 3, 3, "wood")
        c.blob(12, 17, 6, 8, body)
        c.blob(12, 6, 4, 4, body)
        c.stick((4, 15), (20, 15), 2, 2, "wood")
    if tier == "burrow":
        c.blob(16, 29, 12, 7, "stone")
        c.stick((10, 26), (14, 30), 0.8, 0.8, "slate")
    elif tier == "hideout":
        dummy("earth")
        c.blob(26, 32, 4.5, 3.5, "stone")
        c.blob(26, 26, 3.8, 3, "stone")
    else:
        for x in (21, 30):
            c.stick((x, 35), (x, 8), 2.4, 2.4, "dark")
        c.box(20, 12, 31, 14, "dark")
        c.stick((24, 34), (24, 4), 1.4, 1, "wood")                     # a spear on the rack
        c.poly([(23, 4), (25, 4), (24, 0)], "iron")
        c.stick((28, 34), (28, 12), 1.4, 1.4, "iron")                  # a sword
        c.box(26.5, 13, 29.5, 14, "iron")
        dummy("cloth")
        for p in ((12, 14), (11, 16), (13, 16), (12, 18), (12, 5)):    # enchanted: amber runes
            c.px(*p, "#ffb35c")


# ---------------- 7. Hearth (fire animates over 4 frames): campfire ring -> stone hearth with pot -> carved fireplace
@item("hearth", 44, 36, [22, 35], frames=4)
def hearth(c, tier, f):
    if tier == "burrow":
        c.stick((12, 33), (32, 28), 3, 3, "wood")
        c.stick((12, 28), (32, 33), 3, 3, "wood")
        flames(c, 22, 31, 14, f)
        for x in range(6, 40, 6):
            c.blob(x, 33, 3.2, 2.6, "stone")
    elif tier == "hideout":
        c.box(2, 8, 42, 35, "stone")
        c.poly([(9, 35), (9, 18), (14, 13), (30, 13), (35, 18), (35, 35)], "dark", flat=3)
        c.stick((22, 8), (22, 15), 1, 1, "iron")
        c.blob(22, 20, 7, 5, "iron")                                    # the pot
        c.box(14, 15, 30, 16, "iron")
        flames(c, 22, 34, 14, f)
    else:
        c.box(14, 0, 30, 7, "stone")                                    # chimney
        c.box(0, 6, 44, 11, "stone")                                    # mantle
        c.box(2, 11, 9, 35, "stone")
        c.box(35, 11, 42, 35, "stone")
        c.box(9, 11, 35, 35, "dark", flat=3)
        c.stick((12, 34), (32, 30), 3, 3, "wood")
        flames(c, 22, 33, 18, f, 1.3)
        for x in (5, 39):
            c.px(x, 8, "#ffb35c")                                       # carved glyphs on the mantle


# ---------------- 8. Lanterns & decor (flame flickers over 3 frames): candles -> hanging lantern -> rune sconce
@item("decor", 16, 22, [8, 11], frames=3)
def decor(c, tier, f):
    glow = ["#ffd08a", "#ffb35c", "#ffe08a"][f]
    if tier == "burrow":
        for x, top in ((4, 11), (10, 14)):
            c.box(x, top, x + 3, 21, "pink", flat=0)
            c.px(x + 1, top - 1, glow)
            c.px(x + 1, top - 2 - (f % 2), "#ffe08a")
    elif tier == "hideout":
        c.stick((8, 0), (8, 5), 1, 1, "iron")
        c.poly([(4, 7), (12, 7), (8, 4)], "iron")
        c.box(4, 7, 12, 19, "iron")
        c.box(6, 9, 10, 17, "warm", flat=f % 2)
        c.px(8, 12, "#ffe08a")
        c.box(4, 19, 12, 20, "iron")
    else:
        c.box(5, 11, 11, 21, "iron")                                    # wall plate
        c.poly([(2, 9), (14, 9), (11, 13), (5, 13)], "iron")            # bowl
        c.poly([(5, 9), (11, 9), (8, 2 + f)], "fire", flat=1)
        c.poly([(6.5, 9), (9.5, 9), (8, 5 + f)], "fire", flat=0)
        for p in ((8, 15), (7, 16), (9, 16), (8, 17), (8, 18)):
            c.px(*p, "#ffb35c")


# ---------------- 9. Garden (on the surface): dug patch -> raised beds -> glowing mushroom-and-herb grove
@item("garden", 56, 16, [28, 15])
def garden(c, tier, f):
    if tier == "burrow":
        c.blob(28, 12, 26, 4, "soil")
        for x in range(8, 50, 8):
            c.stick((x, 10), (x + 4, 10), 1, 1, "soil", flat=3)
    elif tier == "hideout":
        for x0 in (1, 30):
            c.box(x0, 8, x0 + 25, 15, "wood")
            c.box(x0 + 1, 6, x0 + 24, 8, "soil")
    else:
        c.blob(28, 13, 27, 3.5, "soil")
        for x, h, mat in ((8, 7, "teal"), (15, 10, "warm"), (22, 6, "teal"), (34, 9, "warm"), (42, 7, "teal"), (49, 5, "teal")):
            c.stick((x, 13), (x, 13 - h), 1.4, 1.4, "parch")
            c.blob(x, 13 - h, 3, 1.8, mat)
        for x in (12, 28, 38, 46):
            c.blob(x, 11, 2.4, 2.6, "moss")                             # herbs


# ---------------- 10. Chalkboard (on the wall): slate on a root -> framed board -> carved stone tablet
@item("chalkboard", 28, 32, [14, 16])
def chalkboard(c, tier, f):
    chalk = "#c9cfd6"
    if tier == "burrow":
        c.poly([(4, 5), (22, 3), (24, 29), (6, 30)], "slate")
        c.stick((24, 30), (26, 6), 3, 2, "wood")
    elif tier == "hideout":
        c.box(2, 2, 26, 28, "wood")
        c.box(4, 4, 24, 26, "slate")
        c.box(4, 28, 24, 30, "wood")                                    # chalk ledge
    else:
        c.poly([(3, 6), (6, 2), (22, 2), (25, 6), (26, 31), (2, 31)], "stone")
        c.box(6, 7, 22, 27, "slate")
    for x in range(8, 20):                                              # his scribbles: a move list
        if x % 3 != 2:
            c.px(x, 11, chalk)
    for x in range(8, 17):
        if x % 4 != 3:
            c.px(x, 15, chalk)
    for x in range(8, 19):
        if x % 3 == 0:
            c.px(x, 19, chalk)


# ---------------- 11. Blueprint board (on the wall): scratched bark -> pinned parchment -> iron-framed drafting board
@item("blueprint", 28, 32, [14, 16])
def blueprint(c, tier, f):
    lines = "#3b2a22"
    if tier == "burrow":
        c.poly([(3, 4), (24, 2), (26, 28), (4, 30)], "wood")
        for y in (9, 14, 19, 24):
            c.stick((7, y), (21, y - 1), 0.8, 0.8, "earth", flat=0)
        return
    if tier == "hideout":
        c.box(2, 2, 26, 30, "dark")
    else:
        c.box(2, 2, 26, 30, "iron")
        c.box(4, 4, 24, 28, "dark")
    c.box(5, 5, 23, 27, "parch")
    for p in ((6, 6), (22, 6), (6, 26), (22, 26)):
        c.px(*p, "#f2a0b0" if tier == "hideout" else "#c9cfd6")         # pins / rivets
    for x in range(8, 21):                                              # a plan: a little building
        c.px(x, 22, lines)
    for y in range(13, 22):
        c.px(9, y, lines)
        c.px(19, y, lines)
    for k in range(6):
        c.px(9 + k, 13 - k // 1 if k < 5 else 8, lines)
        c.px(19 - k, 13 - k // 1 if k < 5 else 8, lines)


# ---------------- 12. Radio (on a little wall shelf): gourd with strings -> wooden music box -> rune-lit gramophone
@item("radio", 24, 24, [12, 12])
def radio(c, tier, f):
    c.box(1, 21, 23, 23, "wood")                                        # the shelf it sits on
    if tier == "burrow":
        c.blob(12, 15, 7, 6, "earth")
        c.stick((12, 10), (14, 2), 3, 2, "earth")
        for x in (11, 13):
            c.stick((x, 3), (x - 0.5, 18), 0.6, 0.6, "parch", flat=0)
    elif tier == "hideout":
        c.box(3, 11, 21, 21, "wood")
        c.poly([(3, 11), (5, 4), (21, 6), (21, 11)], "wood")
        c.stick((21, 15), (24, 15), 1.2, 1.2, "iron")
        for x in range(6, 19, 3):
            c.px(x, 16, "#ffd08a")
    else:
        c.box(5, 15, 19, 21, "dark")
        c.poly([(10, 15), (8, 10), (2, 1), (12, 0), (16, 4), (13, 15)], "earth")   # the horn
        c.blob(7, 4, 3, 2.6, "dark", flat=3)
        for p in ((12, 17), (11, 18), (13, 18), (12, 19)):
            c.px(*p, "#ffb35c")


# ---------------- Scaffold (over a faded outline of the build in progress) and its hammer-dust puff
def scaffold():
    w, h = 52, 44
    c = Canvas(w, h)
    for x in (4, 46):
        c.stick((x, 43), (x, 4), 3.8, 3.8, "wood")
    for y in (12, 28):
        c.stick((2, y), (50, y), 3.6, 3.6, "wood")
    c.stick((6, 40), (44, 14), 3.2, 3.2, "wood")
    for x, y in ((4, 12), (46, 12), (4, 28), (46, 28)):
        c.blob(x, y, 2.2, 2.2, "parch")                                 # rope lashings
    frame = c.finish()
    to_json("scaffold", w, h, [26, 43], {"scaffold": [frame]})
    puffs = []
    for f in range(3):
        p = Canvas(14, 12)
        r = 2 + f * 1.6
        for k in range(5):
            a = k * 1.25 + f
            p.blob(7 + math.cos(a) * r, 7 + math.sin(a) * r * 0.6, 2.4 - f * 0.5, 2 - f * 0.4, "fur", flat=min(3, f + 1))
        puffs.append(p.finish())
    to_json("scaffold_dust", 14, 12, [7, 11], {"dust": puffs})


# ---------------- Damage kit: layered onto damaged buildables, fading out piece by piece during repair
def damage():
    pieces = {}
    c = Canvas(16, 16)                                                  # cracks
    for a, b in (((8, 1), (6, 6)), ((6, 6), (9, 10)), ((9, 10), (7, 15)), ((6, 6), (2, 8)), ((9, 10), (14, 11))):
        c.stick(a, b, 1, 1, "dark", flat=3)
    pieces["cracks"] = [c.g.copy()]                                     # no outline: it's a mark on a surface
    c = Canvas(16, 12)                                                  # scorch
    c.blob(8, 6, 7, 5, "dark", flat=2)
    c.blob(7, 6, 4, 3, "dark", flat=3)
    pieces["scorch"] = [c.g.copy()]
    c = Canvas(16, 8)                                                   # debris
    for x, y, r in ((3, 5, 1.6), (7, 6, 1.2), (11, 5, 1.8), (14, 6, 1)):
        c.blob(x, y, r, r * 0.8, "stone")
    c.stick((5, 3), (10, 2), 1.2, 1.2, "wood")
    pieces["debris"] = [c.finish()]
    c = Canvas(16, 6)                                                   # broken plank
    c.poly([(1, 1), (9, 1), (10, 3), (8, 5), (1, 5)], "wood")
    c.poly([(11, 2), (15, 1), (15, 5), (12, 5), (10.5, 4)], "wood")
    pieces["broken_plank"] = [c.finish()]
    wisps = []
    for f in range(3):                                                  # lingering smoke wisp
        c = Canvas(12, 16)
        for k in range(4):
            c.blob(6 + math.sin(f + k * 1.3) * 2, 13 - k * 3 - f, 2.4 - k * 0.3, 1.8, "fur", flat=min(3, 1 + k // 2))
        wisps.append(c.finish())
    pieces["smoke_wisp"] = wisps
    for name, frames in pieces.items():
        w = max(x for f in frames for x, _ in f) + 1
        h = max(y for f in frames for _, y in f) + 1
        w, h = {"cracks": (16, 16), "scorch": (16, 12), "debris": (16, 8), "broken_plank": (16, 6), "smoke_wisp": (12, 16)}[name]
        to_json(f"damage_{name}", w, h, [w // 2, h // 2], {name: frames})


for name, (w, h, anchor, frames, fn) in ITEMS.items():
    tiers = {}
    for tier in ("burrow", "hideout", "lair"):
        out = []
        for f in range(frames):
            c = Canvas(w, h)
            fn(c, tier, f)
            out.append(c.finish())
        tiers[tier] = out
    to_json(name, w, h, anchor, tiers)
scaffold()
damage()
print(f"{len(ITEMS)} buildables x 3 tiers, scaffold, damage kit")
