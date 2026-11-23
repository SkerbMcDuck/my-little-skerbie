# Builds the mini-game props (ART_BRIEF §9).
# Usage: python tools/build_props.py [word|block|brew|rune|forage ...]
#        then render each art/source/props/<game>/<name>.json with tools/render.py
#
# word   word_sign (a tattered plank sign; "nine_slice" [left, top, right, bottom] says which edges
#        stay fixed when the game stretches it to the word's length), dust_puff [3].
# block  hammer_kid / hammer_adult: a chunky dark-iron maul with a glowing core, one row per element
#        (ice, fire, water, lightning, earth) x 16 angles. Same convention as the gear weapons: grip at
#        the canvas centre, frame k drawn at k*22.5 degrees, frame = round(((aim - 90) mod 360)/22.5) mod 16.
#        pad_<element>: the 4 carved rune-stone thumb pads (fire, water, lightning, earth), idle [1] and
#        pressed [1]. beat_pulse [2]: the arena floor's glow on and between beats.
# brew   cauldron (bubble [4]), the 6 ingredients (mushroom, eye_jar, dragon_scale, crystal, feather,
#        bone), number_tag (a blank carved tag; the game writes the number on it), cursed_aura [3],
#        double_sheen [3], plume [5] (drawn in the swappable zone 1234 so the game tints it per potion),
#        fizzle [4], dump [4].
# rune   tile_<piece>_<state> for straight, corner, tee, cross, dead_end x unlit / lit (purple), plus
#        tile_locked; source_rune (pulse [4]), seal_glyph, seal_burst [6], hint_shimmer [3].
# forage the 6 foods (glowfruit, pear, berries, blueberries, cap_mushroom, brown_mushroom) and rotten,
#        each tumble [2].
import json, math, os, random, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_enemies import Canvas, R, polar, lerp, rot, hsh, colour  # noqa: E402

ROOT = "art/source/props"
R.update({
    "plank":  ["#a8945e", "#7a5636", "#3b2a22", "#17151c"],
    "dust":   ["#bfae8c", "#a8945e", "#8b7a4a", "#5f7a3a"],
    "miron":  ["#5a5e66", "#33303d", "#23212b", "#17151c"],          # dark iron
    "core_ice":       ["#f2f9ff", "#cfe9ff", "#9fc9f0", "#4d5e7a"],
    "core_fire":      ["#ffe08a", "#ffb347", "#ff7a1a", "#c2410c"],
    "core_water":     ["#8ff0e6", "#2ec4b6", "#178f86", "#1f3d44"],
    "core_lightning": ["#ffffff", "#fff4b0", "#ffe14d", "#a8945e"],
    "core_earth":     ["#a8945e", "#8b7a4a", "#5f7a3a", "#2c4234"],
    "padstone": ["#5a5e66", "#4d5e7a", "#3b4a63", "#2a3448"],
    "cauld":  ["#5a5e66", "#33303d", "#23212b", "#17151c"],
    "brew":   ["#8ff0e6", "#2ec4b6", "#178f86", "#1f3d44"],          # the bubbling brew
    "glass":  ["#cfe9ff", "#9fc9f0", "#4d5e7a", "#2a3448"],
    "scale":  ["#8ff0e6", "#2ec4b6", "#178f86", "#1f3d44"],
    "crys":   ["#e2b8ff", "#c77dff", "#9b4dff", "#6a2cc9"],
    "feath":  ["#ffc8a8", "#f2a0b0", "#4a3a5c", "#2a2036"],
    "cap":    ["#ffc8a8", "#f2a0b0", "#4a3a5c", "#2a2036"],
    "stem":   ["#bfae8c", "#a8945e", "#8b7a4a", "#3b2a22"],
    "curse":  ["#e4f27a", "#c8e04a", "#2c4234", "#17151c"],
    "gold":   ["#ffe08a", "#f2c14e", "#a8643a", "#3b2a22"],
    "plume":  ["#e2b8ff", "#c77dff", "#9b4dff", "#6a2cc9"],          # default plume colour; it's the zone 1234
    "smoke":  ["#8a8494", "#615b6b", "#433e4c", "#2c2833"],
    "tile":   ["#4d5e7a", "#3b4a63", "#2a3448", "#17151c"],
    "chan":   ["#3a2d4a", "#2a2036", "#23212b", "#17151c"],          # an unlit channel, carved and dark
    "mind":   ["#e2b8ff", "#c77dff", "#9b4dff", "#6a2cc9"],          # Mind-magic purple (lit channel)
    "iron":   ["#c9cfd6", "#5a5e66", "#33303d", "#17151c"],
    "fruitA": ["#ffe08a", "#ffb35c", "#ff8a3d", "#c2410c"],          # glowfruit
    "fruitP": ["#ffc8a8", "#f2a0b0", "#4a3a5c", "#2a2036"],          # pink pear
    "berry":  ["#ffc8a8", "#f2a0b0", "#4a3a5c", "#2a2036"],
    "blue":   ["#8ff0e6", "#2ec4b6", "#178f86", "#1f3d44"],
    "brownm": ["#a8945e", "#8b7a4a", "#5f7a3a", "#3b2a22"],
    "rotten": ["#4a3a5c", "#33303d", "#23212b", "#17151c"],
    "leafp":  ["#557a5c", "#3e5a46", "#2c4234", "#1f3d44"],
    "fly":    ["#23212b", "#17151c", "#17151c", "#17151c"],
})
ELEMENTS = ("ice", "fire", "water", "lightning", "earth")


def write(game, name, w, h, anims, zone=None, extra=None):
    os.makedirs(f"{ROOT}/{game}", exist_ok=True)
    pal, inv = {"o": "#0f0d14"}, {("o",): "o"}
    if zone:
        for i, ch in enumerate("1234"):
            pal[ch] = R[zone][i]
            inv[(zone, i)] = ch
    chars = iter("abcdfghijklmnpqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ056789")
    for frames in anims.values():
        for fr in frames:
            for tok in fr.values():
                if tok not in inv:
                    col = colour(tok)
                    hit = next((k for k, v in pal.items() if v == col and k not in "1234"), None)
                    if hit is None:
                        hit = next(chars)
                        pal[hit] = col
                    inv[tok] = hit
    grids = {a: [["".join(inv[fr[(x, y)]] if (x, y) in fr else "." for x in range(w)) for y in range(h)]
                 for fr in frames] for a, frames in anims.items()}
    d = {"width": w, "height": h, "fps": 8, "palette": pal, "dye_zones": {"tint": "1234"} if zone else {},
         "attach": {}, "animations": grids}
    d.update(extra or {})
    json.dump(d, open(f"{ROOT}/{game}/{name}.json", "w"))
    print("wrote", game, name)


def soft(cells, ramp, cx, cy, r):
    # Shade a soft (unoutlined) round puff: lit core top-left, darker rim.
    g = {}
    for (x, y) in cells:
        d = math.hypot(x + .5 - cx, y + .5 - cy) / max(r, .5)
        lit = ((x + .5 - cx) * -0.6 + (y + .5 - cy) * -0.8) / max(r, .5)
        g[(x, y)] = (ramp, 0 if lit > 0.35 and d < 0.8 else 1 if d < 0.75 else 2 if d < 0.95 else 3)
    return g


def puff(g, cx, cy, r, ramp, w, h):
    cells = [(x, y) for y in range(int(cy - r) - 1, int(cy + r) + 2) for x in range(int(cx - r) - 1, int(cx + r) + 2)
             if math.hypot(x + .5 - cx, y + .5 - cy) <= r and 0 <= x < w and 0 <= y < h]
    g.update(soft(cells, ramp, cx, cy, r))


# ============================================================================ Word Rush
def word():
    W, H = 48, 22
    c = Canvas(W, H)
    c.poly([(1, 10), (47, 10), (47, 17), (2, 18)], "plank", flat=1)              # two planks, evenly lit
    c.poly([(1, 3), (46, 2), (46, 10), (1, 10)], "plank", flat=1)
    for x0, y0, dx in ((6, 1, 3), (40, 0, 3)):                                   # nails
        c.px(x0, y0 + 5, "iron", 1)
        c.px(x0, y0 + 13, "iron", 1)
    g = c.finish()
    for x in range(3, 46):                                                       # the seam between the planks
        g[(x, 10)] = ("plank", 3)
    for x, y in ((47, 17), (46, 18), (2, 18), (1, 17), (24, 18), (33, 18)):      # tattered, chipped edges
        g.pop((x, y), None)
    for x in (12, 13, 30, 31, 32):
        g[(x, 19 - (x % 2))] = ("o",)
        g[(x, 17)] = ("plank", 3)
    for x in range(3, 46):                                                       # lit top edges of each plank
        if (x, 3) in g and g[(x, 3)][0] == "plank":
            g[(x, 3)] = ("plank", 0)
        if (x, 11) in g and g[(x, 11)][0] == "plank":
            g[(x, 11)] = ("plank", 0)
    for x in range(4, 44, 7):                                                    # grain
        g[(x, 6)] = ("plank", 2)
        g[(x + 3, 14)] = ("plank", 2)
    write("word", "word_sign", W, H, {"sign": [g]}, extra={"nine_slice": [6, 4, 6, 4], "anchor": [24, 21]})
    frames = []
    for f in range(3):                                                           # dust puff on a knockback
        g = {}
        for k in range(6):
            a = math.radians(180 + k * 36)
            d = 3 + f * 4
            puff(g, 16 + d * math.cos(a) * 1.3, 14 + d * math.sin(a) * 0.6 - f, 3.5 - f * 0.8 + (k % 2), "dust", 32, 18)
        frames.append(g)
    write("word", "dust_puff", 32, 18, {"puff": frames}, extra={"anchor": [16, 17]})


# ============================================================================ Block Party
def hammer(size, k, element):
    S = 1.0 if size == 64 else 0.7
    c = Canvas(size, size)
    ctr = (size / 2, size / 2)
    ang = k * 22.5

    def P(pts):
        return rot([(x * S, y * S) for x, y in pts], ctr, ang)

    c.poly(P([(-6, -1.6), (14, -1.8), (14, 1.8), (-6, 1.6)]), "plank")           # wooden haft
    c.poly(P([(-8, -2.4), (-5, -2.4), (-5, 2.4), (-8, 2.4)]), "miron")             # pommel
    c.poly(P([(13, -8), (26, -9), (27, 9), (13, 8)]), "miron")                     # the maul head
    c.poly(P([(12, -9), (15, -9), (15, 9), (12, 9)]), "miron", dark=1)              # its iron collar
    c.poly(P([(24, -10), (28, -10), (28, 10), (24, 10)]), "miron", dark=1)          # striking face band
    g = c.finish()
    core = "core_" + element
    r_ = math.radians(-ang)
    for (qx, qy), tok in list(g.items()):                                         # the glowing core, set in the head:
        lx = (qx + .5 - ctr[0]) * math.cos(r_) - (qy + .5 - ctr[1]) * math.sin(r_)   # map each pixel back into the
        ly = (qx + .5 - ctr[0]) * math.sin(r_) + (qy + .5 - ctr[1]) * math.cos(r_)   # hammer's own coordinates
        if tok[0] == "miron" and 16 * S <= lx <= 23.5 * S and abs(ly) <= 5.5 * S:
            d = math.hypot(lx - 19.75 * S, ly) / (5.5 * S)
            g[(qx, qy)] = (core, 0 if d < 0.4 else 1 if d < 0.75 else 2)
    return g


def pad(element, pressed):
    W = H = 40
    c = Canvas(W, H)
    dy = 2 if pressed else 0
    c.poly([(6, 12 + dy), (12, 5 + dy), (28, 5 + dy), (34, 12 + dy), (34, 30 + dy), (28, 36), (12, 36), (6, 30 + dy)], "padstone")
    c.poly([(9, 13 + dy), (13, 8 + dy), (27, 8 + dy), (31, 13 + dy), (31, 28 + dy), (27, 32 + dy), (13, 32 + dy), (9, 28 + dy)],
           "padstone", flat=1)                                                       # the carved top face
    g = c.finish()
    core = "core_" + element
    lv = 0 if pressed else 1
    glyph = {
        "fire":      [((20, 12), (16, 24)), ((16, 24), (20, 28)), ((20, 28), (24, 24)), ((24, 24), (20, 12)), ((20, 18), (20, 26))],
        "water":     [((20, 11), (14, 22)), ((14, 22), (20, 29)), ((20, 29), (26, 22)), ((26, 22), (20, 11))],
        "lightning": [((23, 11), (16, 21)), ((16, 21), (23, 21)), ((23, 21), (17, 30))],
        "earth":     [((13, 26), (20, 13)), ((20, 13), (27, 26)), ((27, 26), (13, 26)), ((16, 21), (24, 21))],
    }[element]
    for (ax, ay), (bx, by) in glyph:
        n = int(max(abs(bx - ax), abs(by - ay))) + 1
        for t in range(n + 1):
            x, y = int(round(ax + (bx - ax) * t / n)), int(round(ay + (by - ay) * t / n + dy))
            g[(x, y)] = (core, lv)
            if pressed:                                                              # a glow halo when pressed
                for ddx, ddy in ((1, 0), (0, 1)):
                    q = (x + ddx, y + ddy)
                    if q in g and g[q][0] == "padstone":
                        g[q] = (core, 2)
    return g


def beat_pulse(f):
    # The arena's ring seams light up on the beat (frame 0) and fade between beats (frame 1).
    W = H = 192
    g = {}
    cx = cy = 96
    for ring in range(1, 7):
        rr = min(91.5, ring * 14 + (0 if f == 0 else 2))
        for a10 in range(0, 3600, 2):
            a = math.radians(a10 / 10)
            x, y = int(round(cx + rr * math.cos(a))), int(round(cy + rr * math.sin(a)))
            if f == 0 or hsh(x, y, 7) < 0.45:
                g[(x, y)] = ("core_ice", (1 if ring < 4 else 2) if f == 0 else 3)
    return g


def block():
    for size, name in ((48, "hammer_kid"), (64, "hammer_adult")):
        write("block", name, size, size, {el: [hammer(size, k, el) for k in range(16)] for el in ELEMENTS},
              extra={"grip": [size // 2, size // 2], "angle_step": 22.5})
    for el in ("fire", "water", "lightning", "earth"):
        write("block", f"pad_{el}", 40, 40, {"idle": [pad(el, False)], "pressed": [pad(el, True)]}, extra={"anchor": [20, 20]})
    write("block", "beat_pulse", 192, 192, {"pulse": [beat_pulse(f) for f in range(2)]}, extra={"anchor": [96, 96]})


# ============================================================================ Potion Brew
def cauldron(f):
    W, H = 72, 60
    c = Canvas(W, H)
    c.stick((10, 59), (16, 46), 4, 3, "cauld")                                    # legs
    c.stick((62, 59), (56, 46), 4, 3, "cauld")
    c.blob(36, 38, 30, 19, "cauld")                                              # the pot
    c.poly([(5, 22), (67, 22), (66, 27), (6, 27)], "cauld")                       # the rim
    c.stick((4, 24), (0, 18), 3, 3, "iron")                                       # handle lugs
    c.stick((68, 24), (72, 18), 3, 3, "iron")
    g = c.finish()
    for x in range(8, 65):                                                       # the brew's surface inside the rim
        for y in range(20, 23):
            g[(x, y)] = ("brew", 1 if y == 22 else 2)
    for k, (bx, phase) in enumerate(((18, 0), (32, 1), (46, 2), (56, 3), (26, 2))):   # bubbles rising and popping
        st = (f + phase) % 4
        r = (1.2, 2.2, 3, 0)[st]
        by = 21 - st * 1.5
        if r:
            for y in range(int(by - r) - 1, int(by + r) + 2):
                for x in range(int(bx - r) - 1, int(bx + r) + 2):
                    d = math.hypot(x + .5 - bx, y + .5 - by)
                    if d <= r:
                        g[(x, y)] = ("brew", 0 if (x < bx and y < by) else 1)
                    elif d <= r + 0.9 and (x, y) not in g:
                        g[(x, y)] = ("brew", 3)
        else:
            for dx, dy in ((-3, -3), (3, -4), (0, -6)):                           # the pop: droplets
                g[(bx + dx, int(by + dy))] = ("brew", 0)
    for x, y in ((14, 36), (20, 46), (52, 44), (60, 34)):                        # rivets and soot
        g[(x, y)] = ("iron", 1)
    return g


def ingredient(kind):
    W = H = 24
    c = Canvas(W, H)
    if kind == "mushroom":
        c.poly([(10, 12), (14, 12), (15, 22), (9, 22)], "stem")
        c.poly([(3, 13), (6, 6), (12, 3), (18, 6), (21, 13)], "cap")
    elif kind == "eye_jar":
        c.poly([(6, 6), (18, 6), (19, 22), (5, 22)], "glass")
        c.poly([(5, 3), (19, 3), (19, 6), (5, 6)], "plank")
    elif kind == "dragon_scale":
        c.poly([(12, 2), (21, 9), (18, 20), (12, 23), (6, 20), (3, 9)], "scale")
    elif kind == "crystal":
        c.poly([(12, 1), (17, 8), (15, 22), (9, 22), (7, 8)], "crys")
        c.poly([(6, 12), (9, 15), (8, 22), (4, 22), (3, 15)], "crys", dark=1)
    elif kind == "feather":
        c.poly([(19, 2), (22, 6), (12, 18), (6, 21), (9, 14)], "feath")
        c.stick((5, 22), (20, 4), 1.4, 1.4, "stem")
    elif kind == "bone":
        c.stick((6, 18), (18, 6), 4, 4, "stem")
        for p in ((5, 17), (7, 20), (16, 4), (19, 7)):
            c.blob(p[0], p[1], 2.6, 2.6, "stem")
    g = c.finish()
    if kind == "mushroom":
        for x, y in ((8, 7), (14, 6), (17, 9), (6, 10)):
            g[(x, y)] = ("cap", 0)
    if kind == "eye_jar":                                                        # an eye floating in green brine
        for y in range(9, 21):
            for x in range(7, 18):
                if (x, y) in g and g[(x, y)][0] == "glass" and y > 11:
                    g[(x, y)] = ("brew", 2 if x > 8 else 1)
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            g[(12 + dx, 16 + dy)] = ("stem", 0)
        g[(12, 16)] = ("fruitA", 2)
        g[(13, 16)] = ("o",)
    if kind == "dragon_scale":
        for y in range(6, 21, 4):
            for x in range(6, 19):
                if (x, y) in g and g[(x, y)][0] == "scale" and (x + y) % 3 == 0:
                    g[(x, y)] = ("scale", 3)
    if kind == "feather":
        for t in range(6):
            p = lerp((7, 19), (19, 5), t / 5)
            g[(int(p[0]) + 1, int(p[1]))] = ("feath", 2)
    return g


def number_tag():
    c = Canvas(20, 14)
    c.poly([(3, 1), (17, 1), (19, 7), (17, 13), (3, 13), (1, 7)], "plank")
    g = c.finish()
    g[(4, 7)] = ("o",)                                                            # the string hole
    return g


def aura(kind, f):
    W = H = 32
    g = {}
    for k in range(10):
        a = math.radians(k * 36 + f * 14)
        r = 12 + (k % 2) * 2
        x = 16 + r * math.cos(a)
        y = 17 + r * math.sin(a) - f * 1.5 - (k % 3)
        if kind == "cursed":                                                      # sickly wisps, green over black
            for dy in range(4):
                for dx in (0, 1):
                    g[(int(x) + dx, int(y) + dy)] = ("curse", 3 if dy >= 2 else 1 if (k + dx) % 2 else 0)
            g[(int(x), int(y) - 1)] = ("curse", 2)
        else:                                                                     # a gold sheen: glints round it
            if (k + f) % 3 == 0:
                for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                    g[(int(x) + dx, int(y) + dy)] = ("gold", 0 if dx == dy == 0 else 1)
            else:
                g[(int(x), int(y))] = ("gold", 1)
    return g


def plume(f):
    # A billowing column of coloured smoke climbing out of the cauldron, spreading as it rises.
    W, H = 64, 96
    g = {}
    top = 92 - (f + 1) * 17
    for k in range(22):
        t = hsh(k, 1) ** 0.8
        cy = 94 - t * (94 - top)
        if cy < top:
            continue
        spread = 4 + (94 - cy) * 0.22
        cx = 32 + (hsh(k, 2) - 0.5) * 2 * spread + math.sin(cy * 0.12 + f) * 2
        r = 4 + (94 - cy) * 0.1 + hsh(k, 3) * 3 - (2.5 if f == 4 else 0)
        if r > 1:
            puff(g, cx, cy, r, "plume", W, H)
    if f >= 3:
        for k in range(14):                                                       # sparkles at the top
            x = int(32 + (hsh(k, f) - 0.5) * 52)
            y = int(top - 4 + hsh(k, 2, f) * 24)
            if 0 <= y < H:
                g[(x, y)] = ("plume", 0)
    return g


def fizzle(f):
    W, H = 48, 40
    g = {}
    for k in range(4):
        if k > f + 1:
            continue
        puff(g, 24 + (k - 1.5) * 7, 34 - k * 5 - f * 2, 4 + k - f * 0.5, "smoke", W, H)
    for k in range(5):                                                            # spitting sparks
        x, y = int(10 + hsh(k, f) * 28), int(10 + hsh(k, 3, f) * 18)
        g[(x, y)] = ("smoke", 0)
    return g


def dump(f):
    W, H = 80, 40
    g = {}
    for k in range(10):                                                           # brew sloshing out over both sides
        side = -1 if k % 2 else 1
        t = (f + 1) / 4
        x = 40 + side * (6 + k * 3) * t * 1.6
        y = 12 + (k * 2) * t + f * f * 1.6
        r = 3.2 - k * 0.15
        if y < H:
            puff(g, x, y, r, "brew", W, H)
    if f == 3:
        for x in range(4, 76):
            g[(x, H - 1)] = ("brew", 2 if 8 < x < 72 else 3)
    return g


def brew():
    write("brew", "cauldron", 72, 60, {"bubble": [cauldron(f) for f in range(4)]}, extra={"anchor": [36, 59]})
    for kind in ("mushroom", "eye_jar", "dragon_scale", "crystal", "feather", "bone"):
        write("brew", kind, 24, 24, {"idle": [ingredient(kind)]}, extra={"anchor": [12, 23]})
    write("brew", "number_tag", 20, 14, {"tag": [number_tag()]}, extra={"anchor": [10, 0]})
    write("brew", "cursed_aura", 32, 32, {"aura": [aura("cursed", f) for f in range(3)]}, extra={"anchor": [16, 31]})
    write("brew", "double_sheen", 32, 32, {"sheen": [aura("gold", f) for f in range(3)]}, extra={"anchor": [16, 31]})
    write("brew", "plume", 64, 96, {"plume": [plume(f) for f in range(5)]}, zone="plume", extra={"anchor": [32, 95]})
    write("brew", "fizzle", 48, 40, {"fizzle": [fizzle(f) for f in range(4)]}, extra={"anchor": [24, 39]})
    write("brew", "dump", 80, 40, {"dump": [dump(f) for f in range(4)]}, extra={"anchor": [40, 0]})


# ============================================================================ Rune Lock
CONNECT = {"straight": "NS", "corner": "NE", "tee": "NEW", "cross": "NESW", "dead_end": "N"}


def tile(piece, lit, locked=False):
    T = 36
    c = Canvas(T, T)
    c.poly([(1, 1), (34, 1), (34, 34), (1, 34)], "tile")
    g = c.finish()
    for x in range(3, 33):                                                        # a bevelled face
        g[(x, 2)] = ("tile", 0)
        g[(x, 33)] = ("tile", 3)
    for y in range(3, 33):
        g[(2, y)] = ("tile", 0)
        g[(33, y)] = ("tile", 3)
    for x, y in ((6, 28), (27, 7), (10, 9), (29, 26)):                           # wear
        g[(x, y)] = ("tile", 2)
    if piece:
        ramp = "mind" if lit else "chan"
        arms = {"N": (18, 0), "S": (18, 35), "E": (35, 18), "W": (0, 18)}
        pts = []
        for d in CONNECT[piece]:
            ex, ey = arms[d]
            n = 18
            for t in range(n + 1):
                pts.append((int(round(18 + (ex - 18) * t / n)), int(round(18 + (ey - 18) * t / n))))
        for (x, y) in pts:
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    q = (x + dx, y + dy)
                    if 1 <= q[0] <= 34 and 1 <= q[1] <= 34:
                        edge = abs(dx) == 2 or abs(dy) == 2
                        g[q] = (ramp, (2 if edge else 0 if (dx, dy) == (0, 0) else 1)) if lit else ("chan", 3 if edge else 1)
        hub = 4 if piece == "dead_end" else 3                                      # the hub (a socket for a dead end)
        for dx in range(-hub, hub + 1):
            for dy in range(-hub, hub + 1):
                if abs(dx) + abs(dy) <= hub + 1:
                    g[(18 + dx, 18 + dy)] = (ramp, 1 if lit else 2) if abs(dx) + abs(dy) <= hub - 1 else (ramp if lit else "chan", 3 if not lit else 2)
    if locked:                                                                     # iron bands bolted across the face
        for y0 in (9, 25):
            for x in range(1, 35):
                for y in range(y0, y0 + 3):
                    g[(x, y)] = ("iron", 1 if y == y0 else 2)
            for x in (5, 30):
                g[(x, y0 + 1)] = ("iron", 0)
        for dx in range(-3, 4):                                                    # a padlock in the middle
            for dy in range(-2, 4):
                g[(18 + dx, 18 + dy)] = ("gold", 1 if dy < 1 else 2)
        g[(18, 19)] = ("o",)
        for dx in (-2, 2):
            g[(18 + dx, 15)] = ("iron", 1)
            g[(18 + dx, 14)] = ("iron", 1)
        g[(17, 13)] = ("iron", 1)
        g[(18, 13)] = ("iron", 1)
        g[(19, 13)] = ("iron", 1)
    return g


def source_rune(f):
    W = H = 32
    c = Canvas(W, H)
    c.blob(16, 16, 13, 13, "tile")
    g = c.finish()
    glow = (1, 0, 1, 2)[f]
    for a10 in range(0, 3600, 20):                                               # a ring and a radiant glyph, pulsing
        a = math.radians(a10 / 10)
        g[(int(round(16 + 9 * math.cos(a))), int(round(16 + 9 * math.sin(a))))] = ("mind", glow + 1 if glow < 3 else 3)
    for k in range(6):
        a = math.radians(k * 60 + 30)
        for t in range(2, 7):
            g[(int(round(16 + t * math.cos(a))), int(round(16 + t * math.sin(a))))] = ("mind", glow)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            g[(16 + dx, 16 + dy)] = ("mind", 0)
    if f == 1:
        for k in range(8):
            a = math.radians(k * 45)
            g[(int(round(16 + 14 * math.cos(a))), int(round(16 + 14 * math.sin(a))))] = ("mind", 1)
    return g


def seal_glyph(lit):
    W = H = 40
    c = Canvas(W, H)
    c.blob(20, 20, 18, 18, "tile")
    g = c.finish()
    ramp = "mind" if lit else "chan"
    for a10 in range(0, 3600, 15):
        a = math.radians(a10 / 10)
        for rr in (15, 11):
            g[(int(round(20 + rr * math.cos(a))), int(round(20 + rr * math.sin(a))))] = (ramp, 1 if lit else 2)
    for (ax, ay), (bx, by) in (((20, 9), (20, 31)), ((11, 20), (29, 20)), ((13, 13), (27, 27)), ((27, 13), (13, 27))):
        n = int(max(abs(bx - ax), abs(by - ay)))
        for t in range(n + 1):
            x, y = int(round(ax + (bx - ax) * t / n)), int(round(ay + (by - ay) * t / n))
            if math.hypot(x - 20, y - 20) < 10:
                g[(x, y)] = (ramp, 0 if lit else 1)
    return g


def seal_burst(f):
    W = H = 64
    g = {}
    base = {(x + 12, y + 12): t for (x, y), t in seal_glyph(True).items()}
    if f == 0:
        g.update(base)
        for k in range(12):                                                       # cracks of light
            a = math.radians(k * 30)
            for t in range(12, 20):
                g[(int(32 + t * math.cos(a)), int(32 + t * math.sin(a)))] = ("mind", 0)
        return g
    keep = (0.7, 0.4, 0.15, 0, 0)[f - 1]
    for p, t in base.items():
        if hsh(*p, 3) < keep:
            ang = math.atan2(p[1] - 32, p[0] - 32)
            d = f * 3
            g[(int(p[0] + math.cos(ang) * d), int(p[1] + math.sin(ang) * d))] = t
    for k in range(8):                                                            # smoke billowing out
        a = math.radians(k * 45 + f * 10)
        d = 6 + f * 5
        r = 4 + f * 1.2 - (3 if f == 5 else 0)
        if r > 0:
            puff(g, 32 + d * math.cos(a), 32 + d * math.sin(a) - f, r, "smoke", W, H)
    return g


def hint_shimmer(f):
    T = 36
    g = {}
    for k in range(T * 2):                                                        # a diagonal band of light sweeping across
        x = k % T
        y = (k * 7) % T
    for y in range(T):
        for x in range(T):
            band = (x + y) - (f * 24 - 12)
            if abs(band) < 3 and (x in (0, 1, T - 2, T - 1) or y in (0, 1, T - 2, T - 1) or abs(band) < 1.5):
                g[(x, y)] = ("gold", 0 if abs(band) < 1.2 else 1)
    return g


def rune():
    for piece in CONNECT:
        for lit in (False, True):
            write("rune", f"tile_{piece}_{'lit' if lit else 'unlit'}", 36, 36, {"tile": [tile(piece, lit)]})
    write("rune", "tile_locked", 36, 36, {"tile": [tile("straight", False, locked=True)]})
    write("rune", "source_rune", 32, 32, {"pulse": [source_rune(f) for f in range(4)]}, extra={"anchor": [16, 16]})
    write("rune", "seal_glyph", 40, 40, {"unlit": [seal_glyph(False)], "lit": [seal_glyph(True)]}, extra={"anchor": [20, 20]})
    write("rune", "seal_burst", 64, 64, {"burst": [seal_burst(f) for f in range(6)]}, extra={"anchor": [32, 32]})
    write("rune", "hint_shimmer", 36, 36, {"shimmer": [hint_shimmer(f) for f in range(3)]})


# ============================================================================ Foraging
def food(kind, f):
    W = H = 16
    c = Canvas(W, H)
    a = (0, 25)[f]                                                                 # the tumble: rotated a little

    def P(pts):
        return rot([(x - 8, y - 8) for x, y in pts], (8, 8), a)

    if kind == "glowfruit":
        c.blob(*P([(8, 9)])[0], 5.5, 5.5, "fruitA")
        c.stick(*P([(8, 4), (9, 1)]), 1.4, 1.2, "stem")
        c.poly(P([(9, 3), (14, 1), (12, 4)]), "leafp")
    elif kind == "pear":
        c.blob(*P([(8, 10)])[0], 5, 4.5, "fruitP")
        c.blob(*P([(8, 6)])[0], 3, 3, "fruitP")
        c.stick(*P([(8, 3), (7, 0)]), 1.4, 1.2, "stem")
    elif kind == "berries":
        for p in ((6, 9), (10, 9), (8, 12), (8, 6), (5, 12), (11, 12)):
            c.blob(*P([p])[0], 2.3, 2.3, "berry")
        c.poly(P([(7, 4), (12, 1), (10, 5)]), "leafp")
    elif kind == "blueberries":
        for p in ((6, 10), (10, 10), (8, 7), (8, 13)):
            c.blob(*P([p])[0], 2.6, 2.6, "blue")
        c.stick(*P([(8, 5), (8, 2)]), 1.2, 1.2, "stem")
    elif kind == "cap_mushroom":
        c.poly(P([(6, 8), (10, 8), (10.5, 15), (5.5, 15)]), "stem")
        c.poly(P([(1, 9), (3, 4), (8, 2), (13, 4), (15, 9)]), "cap")
    elif kind == "brown_mushroom":
        c.poly(P([(6, 9), (10, 9), (10, 15), (6, 15)]), "stem")
        c.poly(P([(2, 10), (4, 5), (8, 3), (12, 5), (14, 10)]), "brownm")
    elif kind == "rotten":
        c.blob(*P([(8, 10)])[0], 5.5, 4.8, "rotten")
        c.stick(*P([(8, 5), (6, 2)]), 1.4, 1.2, "stem", dark=2)
    g = c.finish()
    hi = P([(6, 7)])[0]
    if kind in ("glowfruit", "pear"):
        g[(int(hi[0]), int(hi[1]))] = ("fruitA" if kind == "glowfruit" else "fruitP", 0)
    if kind == "cap_mushroom":
        for p in ((5, 5), (10, 4), (12, 7)):
            q = P([p])[0]
            g[(int(q[0]), int(q[1]))] = ("stem", 0)
    if kind == "rotten":                                                           # wrinkles, a mould spot, buzzing flies
        for p in ((6, 9), (9, 11), (7, 12), (10, 8)):
            q = P([p])[0]
            g[(int(q[0]), int(q[1]))] = ("rotten", 3)
        q = P([(10, 11)])[0]
        g[(int(q[0]), int(q[1]))] = ("curse", 2)
        for k, (x, y) in enumerate(((2, 2), (13, 3), (14, 8)) if f == 0 else ((3, 3), (12, 1), (1, 7))):
            g[(x, y)] = ("fly", 0)
            g[(x + 1, y - 1 if k % 2 else y)] = ("smoke", 1)
    return g


def forage():
    for kind in ("glowfruit", "pear", "berries", "blueberries", "cap_mushroom", "brown_mushroom", "rotten"):
        write("forage", kind, 16, 16, {"tumble": [food(kind, f) for f in range(2)]}, extra={"anchor": [8, 8]})


GAMES = {"word": word, "block": block, "brew": brew, "rune": rune, "forage": forage}
if __name__ == "__main__":
    for n in sys.argv[1:] or list(GAMES):
        GAMES[n]()
