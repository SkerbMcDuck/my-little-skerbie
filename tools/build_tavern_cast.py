# Builds the tavern's cast and props (ART_BRIEF §8): the badger bartender, the druid ringmaster,
# the druid's ring-of-light effect, the breakables (chair, mug) and the two crowd rows.
# Usage: python tools/build_tavern_cast.py
#        then render each art/source/tavern/<name>.json with tools/render.py
#
#   badger     96x52  idle [3] (polishing a mug), slide_coins [4]. Upper body only: the bottom row
#                     sits on the bar top (spot "badger"); "anchor" is that bottom-centre pixel.
#                     A hulking one-eyed badger (a leather patch over one eye) in a stained apron.
#   druid      48x72  idle [3], summon [5]. Hooded, antlered, a gnarled staff; green runes on the
#                     robe and staff glow as he summons.
#   ring_light 96x48  the ring of light on the floor [5] (the druid's summon, a beast's summon-in
#                     and its KO poof); "anchor" = the bottom-centre, on the floor under the beast.
#   chair      28x28  intact [1], smash [3];   mug  16x16  intact [1], smash [3]
#   crowd_front 225x44 and crowd_gallery 194x24: silhouetted critters, cheer [2] and erupt [2].
#                     "anchor" = bottom-centre (spots "crowd_front" / "crowd_gallery").
# Same house style as the characters; NPC and beast eyes are warm amber.
import json, math, os, random, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_enemies import Canvas, R, polar, lerp, rot, hsh, colour  # noqa: E402

OUT = "art/source/tavern"
os.makedirs(OUT, exist_ok=True)
R.update({
    "bfur":   ["#615b6b", "#433e4c", "#2c2833", "#17151c"],          # badger: dark grey
    "bwhite": ["#c9cfd6", "#8a8494", "#615b6b", "#433e4c"],          # badger stripe and cheeks
    "apron":  ["#bfae8c", "#a8945e", "#8b7a4a", "#7a5636"],
    "gold":   ["#ffe08a", "#f2c14e", "#a8643a", "#3b2a22"],
    "robe":   ["#3e5a46", "#2c4234", "#1f3d44", "#17151c"],
    "beye":   ["#ffd08a", "#ffb35c", "#ffb35c", "#ffb35c"],
    "light":  ["#ffffff", "#e4f27a", "#c8e04a", "#557a5c"],
    "crowd":  ["#4a3a5c", "#2a2036", "#23212b", "#17151c"],
    "warm":   ["#ffd08a", "#ffb35c", "#ff8a3d", "#c2410c"],
    "ale":    ["#ffd08a", "#ffb35c", "#a8643a", "#7a5636"],
    "foam":   ["#ffc8a8", "#bfae8c", "#a8945e", "#8b7a4a"],
})


def write(name, w, h, anims, extra=None):
    pal, inv = {"o": "#0f0d14"}, {("o",): "o"}
    chars = iter("abcdfghijklmnpqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
    for frames in anims.values():
        for fr in frames:
            for tok in fr.values():
                if tok not in inv:
                    col = colour(tok)
                    hit = next((k for k, v in pal.items() if v == col), None)
                    if hit is None:
                        hit = next(chars)
                        pal[hit] = col
                    inv[tok] = hit
    grids = {a: [["".join(inv[fr[(x, y)]] if (x, y) in fr else "." for x in range(w)) for y in range(h)]
                 for fr in frames] for a, frames in anims.items()}
    d = {"width": w, "height": h, "fps": 8, "palette": pal, "dye_zones": {}, "attach": {}, "animations": grids}
    d.update(extra or {})
    json.dump(d, open(f"{OUT}/{name}.json", "w"))
    print("wrote", name)


# ============================================================================ the badger bartender
def coins(c, x, y, n=4):
    for k in range(n):
        c.poly([(x - 3.5, y - k * 1.6), (x + 3.5, y - k * 1.6), (x + 3.5, y - k * 1.6 - 1.8), (x - 3.5, y - k * 1.6 - 1.8)], "gold")


def badger(anim, f):
    W, H = 96, 52
    c = Canvas(W, H)
    B = H - 1                                                                   # the bar top row
    bob = (0, -1, 0)[f % 3] if anim == "idle" else 0
    cx = 26
    # shoulders and body behind the bar, apron over the chest
    c.poly([(cx - 22, B), (cx - 20, 30 + bob), (cx - 13, 22 + bob), (cx + 13, 22 + bob), (cx + 20, 30 + bob), (cx + 22, B)], "bfur")
    c.poly([(cx - 12, B), (cx - 11, 32 + bob), (cx + 11, 32 + bob), (cx + 12, B)], "apron")
    for x, y in ((cx - 6, 38), (cx + 4, 44), (cx - 2, 47), (cx + 7, 36)):        # stains
        c.px(x, y + bob, "apron", 3)
        c.px(x + 1, y + bob, "apron", 2)
    for sx in (-8, 8):                                                           # apron straps
        c.stick((cx + sx, 32 + bob), (cx + sx * 0.6, 22 + bob), 1.8, 1.8, "apron", flat=2)
    # head: broad and flat, a white stripe down the middle, small round ears
    hx, hy = cx + 2, 13 + bob
    for ex_ in (-11, 11):
        c.blob(hx + ex_, hy - 6, 3.4, 3, "bfur")
    c.blob(hx, hy, 13, 10, "bwhite")                                             # a white face...
    for sx in (-1, 1):                                                           # ...with a black stripe through each eye
        c.poly([(hx + sx * 1.8, hy + 8), (hx + sx * 6.5, hy + 8), (hx + sx * 12, hy - 7), (hx + sx * 4, hy - 10.5)], "bfur")
    c.poly([(hx - 4, hy + 4), (hx + 4, hy + 4), (hx + 2.5, hy + 10), (hx - 2.5, hy + 10)], "bwhite")
    c.blob(hx, hy + 9, 2.4, 1.8, "bfur", flat=3)                                  # nose
    # arms
    if anim == "idle":       # polishing a mug: the mug held in his left paw, the rag circling in the right
        mug_c = (cx + 8, B - 8)
        rag = [(cx + 4, B - 11), (cx + 10, B - 13), (cx + 12, B - 7)][f]
        c.stick((cx - 15, 30 + bob), (cx + 4, B - 5), 8, 6, "bfur")
        c.blob(cx + 5, B - 5, 3.5, 3, "bfur")
        c.poly([(mug_c[0] - 4, mug_c[1] - 6), (mug_c[0] + 4, mug_c[1] - 6), (mug_c[0] + 4, mug_c[1] + 4), (mug_c[0] - 4, mug_c[1] + 4)], "wood")
        c.stick((mug_c[0] + 4, mug_c[1] - 3), (mug_c[0] + 6.5, mug_c[1]), 2, 2, "wood")
        c.stick((cx + 15, 30 + bob), rag, 8, 6, "bfur")
        c.blob(rag[0], rag[1], 4, 3.4, "apron")
    else:                    # sliding a stack of coins along the bar to the right
        coin_x = (34, 46, 66, 88)[f]
        paw = (min(coin_x - 5, 60), B - 3)
        if f == 3:
            paw = (cx + 10, B - 3)
        c.stick((cx - 15, 30), (cx - 8, B - 2), 8, 6, "bfur")
        c.blob(cx - 8, B - 2, 3.5, 3, "bfur")
        c.stick((cx + 15, 30), paw, 8, 6, "bfur")
        c.blob(paw[0], paw[1], 4, 3.2, "bfur")
        coins(c, coin_x, B - 1, 4 if f < 3 else 3)
    g = c.finish()
    # one amber eye on the left; a leather patch with a strap over the right
    ex, ey = hx - 7, hy - 1
    g[(ex, ey)] = ("beye", 0)
    g[(ex + 1, ey)] = ("beye", 1)
    for x in range(ex - 1, ex + 3):
        g[(x, ey - 1)] = ("o",)
    for x in range(hx + 4, hx + 10):
        for y in range(hy - 3, hy + 1):
            g[(x, y)] = ("rust", 0 if y == hy - 3 else 1)
    for k in range(-11, 13):
        g[(hx + k, hy - 6 + (k + 11) // 8)] = ("rust", 2)
    for x in range(hx - 2, hx + 3):                                              # a gruff mouth
        g[(x, hy + 11)] = ("o",)
    return g


# ============================================================================ the druid ringmaster
def druid(anim, f):
    W, H = 48, 72
    c = Canvas(W, H)
    G = H - 1
    bob = (0, -1, 0)[f % 3] if anim == "idle" else 0
    glow = 0
    if anim == "idle":
        staff_a, fist = -95 + (0, 2, -2)[f], (36, 36 + bob)
    else:
        staff_a, fist, glow = [(-95, (30, 34), 1), (-100, (28, 18), 2), (-60, (36, 26), 3), (-60, (36, 26), 3),
                               (-90, (31, 32), 1)][f]
    # robe: a tall hooded cloak, hem on the floor, sleeves
    c.poly([(8, G), (12, 40), (15, 24 + bob), (22, 16 + bob), (30, 18 + bob), (33, 30 + bob), (34, G)], "robe")
    for x in range(9, 34, 4):                                                   # ragged hem
        c.poly([(x, G - 2), (x + 4, G - 2), (x + 2, G + 1)], "robe")
    c.stick((16, 26 + bob), (12, 46 + bob), 6, 5, "robe", dark=1)               # far sleeve
    # antlers rising through the hood
    for base, mid, tips in (((20, 14 + bob), (15, 7 + bob), ((10, 4 + bob), (17, 3 + bob))),
                            ((26, 13 + bob), (30, 6 + bob), ((35, 4 + bob), (28, 3 + bob)))):
        c.stick(base, mid, 2.8, 2.4, "wood")
        for t in tips:
            c.stick(mid, t, 2.4, 1.4, "wood")
    c.blob(24, 17 + bob, 7, 7, "robe")                                          # the hood
    c.poly([(26, 13 + bob), (32, 15 + bob), (31, 23 + bob), (26, 22 + bob)], "crowd", flat=3)   # the shadowed face
    # staff: gnarled wood with a rune-knot at the head
    top, bot = polar(fist, staff_a, 22), polar(fist, staff_a + 180, 28)
    top = (top[0], max(5, top[1]))
    bot = (bot[0], min(G, bot[1]))
    c.stick(bot, top, 3.6, 3, "wood")
    c.stick(top, polar(top, staff_a - 50, 4), 2.6, 1.6, "wood")
    c.stick(top, polar(top, staff_a + 60, 4), 2.6, 1.6, "wood")
    c.blob(top[0], top[1], 2.6, 2.6, "wood")
    c.stick((28, 26 + bob), fist, 6, 5, "robe")                                 # near sleeve to the staff hand
    c.blob(fist[0], fist[1], 2.6, 2.4, "bone")
    g = c.finish()
    # the green rune-light: eye, staff knot, runes down the robe; brighter as he summons
    lv = {0: 3, 1: 2, 2: 1, 3: 0}[glow]
    g[(29, 18 + bob)] = ("light", 1 if glow < 2 else 0)
    tx, ty = int(round(top[0])), int(round(top[1]))
    for dx, dy in ((0, 0), (1, 0), (0, 1), (-1, 0), (0, -1)):
        g[(tx + dx, ty + dy)] = ("light", min(3, lv + (0 if dx == dy == 0 else 1)))
    if glow >= 2:
        for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            g[(tx + dx, ty + dy)] = ("light", 1 if glow == 3 else 2)
    for y0 in (36, 46, 56):                                                     # runes down the robe front
        for dx, dy in ((0, 0), (1, 1), (0, 2), (-1, 1), (0, 3)):
            q = (24 + dx, y0 + dy + (bob if y0 < 40 else 0))
            if q in g and g[q][0] == "robe":
                g[q] = ("light", min(3, lv + 1))
    return g


# ============================================================================ ring of light
def ring_light(f):
    W, H = 96, 48
    g = {}
    cx, base = W // 2, H - 6
    rx = (6, 20, 34, 42, 46)[f]
    ry = rx * 0.28
    fade = (0, 0, 0, 1, 2)[f]
    for a10 in range(0, 3600, 4):
        a = math.radians(a10 / 10)
        for dr in (0, 1):
            x = int(round(cx + (rx - dr) * math.cos(a)))
            y = int(round(base + (ry - dr * 0.4) * math.sin(a)))
            if 0 <= x < W and 0 <= y < H:
                g[(x, y)] = ("light", min(3, fade + dr))
    if f in (1, 2, 3):                                                          # shafts of light rising from the ring
        for k in range(9):
            a = math.radians(k * 40 + f * 13)
            x = int(round(cx + rx * 0.85 * math.cos(a)))
            y0 = int(round(base + ry * 0.85 * math.sin(a)))
            ht = (10, 26, 18)[f - 1] * (0.6 + 0.4 * hsh(k, f))
            for y in range(int(y0 - ht), y0):
                if hsh(x, y, f) < 0.8 and 0 <= y < H:
                    g[(x, y)] = ("light", 1 if y > y0 - ht * 0.5 else 2 + (f == 3))
    for k in range(int((4, 12, 18, 14, 8)[f])):                                 # rising motes
        x = int(cx + (hsh(k, 1, f) - 0.5) * rx * 2)
        y = int(base - hsh(k, 2, f) * (8 + f * 8))
        if 0 <= x < W and 0 <= y < H:
            g[(x, y)] = ("light", 0 if hsh(k, 3) < 0.3 else 1 + (f >= 3))
    return g


# ============================================================================ breakables
def chair(frame):
    W, H = 28, 28
    c = Canvas(W, H)
    G = H - 1
    if frame == 0:                                                              # intact: a stout tavern chair, side view
        c.stick((8, 4), (8, G), 3, 3, "wood")                                   # back post
        for y in (6, 11):
            c.stick((8, y), (12, y), 2.4, 2.4, "wood")
        c.poly([(7, 15), (21, 15), (21, 18), (7, 18)], "wood")                  # seat
        c.stick((19, 18), (20, G), 3, 3, "wood")
        c.stick((10, 18), (10, G), 3, 3, "wood", dark=1)
        return c.finish()
    pieces = [("post", (8, 4), (8, G)), ("seat", (7, 15), (21, 18)), ("leg", (19, 18), (20, G)), ("rung", (8, 6), (12, 6))]
    s = frame                                                                    # 1 splintering, 2 flying, 3 on the floor
    for i, (kind, a, b) in enumerate(pieces):
        mid = lerp(a, b, 0.5)
        vx, vy = ((-1, -1), (0, -1.5), (1.2, -0.5), (-1.5, -1.8))[i]
        if s == 3:
            x = 4 + i * 6
            c.stick((x, G - 1), (x + (7 if kind != "rung" else 4), G - 1 - (i % 2)), 3, 3, "wood")
            continue
        t = (2, 6)[s - 1]
        dx, dy = vx * t, vy * t + (0 if s == 1 else 2)
        ang = (i * 35 + 20) * (s - 1)
        pa, pb = rot([(a[0] - mid[0], a[1] - mid[1]), (b[0] - mid[0], b[1] - mid[1])], (mid[0] + dx, mid[1] + dy), ang)
        if kind == "seat":
            c.stick(pa, pb, 3.2, 3.2, "wood")
        else:
            c.stick(pa, pb, 3, 3, "wood")
    g = c.finish()
    if s < 3:
        for k in range(6):                                                       # splinters
            x = int(14 + (hsh(k, s) - 0.5) * 18 * s)
            y = int(14 + (hsh(k, 9, s) - 0.5) * 12 * s)
            if 0 <= x < W and 0 <= y < H:
                g[(x, y)] = ("wood", 0)
    return g


def mug(frame):
    W, H = 16, 16
    c = Canvas(W, H)
    G = H - 1
    if frame == 0:
        c.poly([(4, 6), (10, 6), (10, G), (4, G)], "wood")
        c.stick((10, 8), (13, 11), 2, 2, "wood")
        c.stick((13, 11), (10, 13), 2, 2, "wood")
        c.poly([(3.5, 4), (10.5, 4), (10.5, 6.5), (3.5, 6.5)], "foam")
        g = c.finish()
        g[(5, 9)] = ("iron", 1)
        g[(5, 12)] = ("iron", 1)
        return g
    if frame == 1:                                                              # knocked: tipping, ale sloshing out
        c.poly(rot([(-3, -5), (3, -5), (3, 5), (-3, 5)], (7, 11), 50), "wood")
        g = c.finish()
        for x, y in ((11, 5), (12, 4), (13, 6), (10, 3), (14, 8)):
            g[(x, y)] = ("ale", 1)
        g[(12, 3)] = ("foam", 0)
        return g
    if frame == 2:                                                              # shattered staves, a splash
        for i, (x, y, a) in enumerate(((3, 10, 30), (8, 7, -40), (12, 11, 70))):
            c.poly(rot([(-1.5, -3), (1.5, -3), (1.5, 3), (-1.5, 3)], (x, y), a), "wood")
        g = c.finish()
        for k in range(8):
            g[(int(2 + hsh(k, 1) * 12), int(3 + hsh(k, 2) * 9))] = ("ale", k % 2)
        return g
    g = {}                                                                       # a puddle and a couple of staves
    for x in range(2, 14):
        g[(x, G)] = ("ale", 2 if x in (2, 13) else 1)
    for x in range(4, 11):
        g[(x, G - 1)] = ("ale", 1)
    c.stick((3, G - 2), (7, G - 3), 2.4, 2.4, "wood")
    c.stick((10, G - 3), (13, G - 1), 2.4, 2.4, "wood")
    g.update(c.finish())
    return g


# ============================================================================ the crowd
KINDS = ("fox", "rabbit", "owl", "toad", "mole", "hedgehog", "deer", "frog", "boarlet", "cat")


def critter(c, kind, x, base, s, up, arms, mug_up, dark):
    # One silhouetted critter: shoulders from the bottom edge, a head shape by kind, ears or horns.
    y = base - up
    c.blob(x, y - 3 * s, 6 * s, 5 * s, "crowd", dark=dark)                       # shoulders
    hy = y - 10 * s
    hr = {"toad": 5.5, "frog": 5, "owl": 5.5, "mole": 4.5, "hedgehog": 5}.get(kind, 4.5) * s
    if kind == "rabbit":
        for dx in (-1.8, 1.8):
            c.poly([(x + dx * s - 1.3 * s, hy - 3 * s), (x + dx * s + 1.3 * s, hy - 3 * s), (x + dx * s * 1.4, hy - 12 * s)], "crowd", dark=dark)
    if kind in ("fox", "cat"):
        for dx in (-3, 3):
            c.poly([(x + dx * s - 2 * s, hy - 2 * s), (x + dx * s + 2 * s, hy - 2 * s), (x + dx * s * 1.2, hy - 8 * s)], "crowd", dark=dark)
    if kind == "owl":
        for dx in (-3.5, 3.5):
            c.poly([(x + dx * s - 1.5 * s, hy - 3 * s), (x + dx * s + 1.5 * s, hy - 3 * s), (x + dx * s * 1.3, hy - 7 * s)], "crowd", dark=dark)
    if kind == "deer":
        for dx in (-1, 1):
            a, b = (x + dx * 2 * s, hy - 3 * s), (x + dx * 5 * s, hy - 10 * s)
            c.stick(a, b, 1.6 * s, 1 * s, "crowd", dark=dark)
            c.stick(lerp(a, b, 0.5), (x + dx * 7 * s, hy - 7 * s), 1.4 * s, 1 * s, "crowd", dark=dark)
    if kind == "hedgehog":
        for k in range(-3, 4):
            a = math.radians(-90 + k * 24)
            c.poly([(x + math.cos(a + .3) * hr, hy + math.sin(a + .3) * hr), (x + math.cos(a - .3) * hr, hy + math.sin(a - .3) * hr),
                    (x + math.cos(a) * hr * 1.6, hy + math.sin(a) * hr * 1.6)], "crowd", dark=dark)
    if kind == "boarlet":
        for dx in (-3.5, 3.5):
            c.blob(x + dx * s, hy - 3 * s, 1.8 * s, 1.6 * s, "crowd", dark=dark)
    c.blob(x, hy, hr * (1.25 if kind in ("toad", "frog") else 1), hr * (0.8 if kind in ("toad", "frog") else 1), "crowd", dark=dark)
    if kind == "frog":
        for dx in (-3, 3):
            c.blob(x + dx * s, hy - 3.5 * s, 2 * s, 2 * s, "crowd", dark=dark)
    for side in arms:                                                              # raised arms, maybe a mug
        sh = (x + side * 5 * s, y - 5 * s)
        hand = (x + side * 7 * s, y - 15 * s - up * 0.3)
        c.stick(sh, hand, 2.6 * s, 2.2 * s, "crowd", dark=dark)
        if mug_up and side > 0:
            c.poly([(hand[0] - 1.5 * s, hand[1] - 3.5 * s), (hand[0] + 2 * s, hand[1] - 3.5 * s), (hand[0] + 2 * s, hand[1]),
                    (hand[0] - 1.5 * s, hand[1])], "wood")
    return (x, hy, hr, kind)


def crowd(width, height, s, n, anim, f, seed):
    c = Canvas(width, height)
    rnd = random.Random(seed)
    G = height - 1 + int(3 * s)                                                   # shoulders run off the bottom edge
    heads = []
    spacing = width / n
    specs = []
    for i in range(n):
        specs.append(dict(x=spacing * (i + 0.5) + rnd.uniform(-spacing * 0.25, spacing * 0.25),
                          kind=rnd.choice(KINDS), sz=s * rnd.uniform(0.85, 1.1), back=i % 2,
                          eyec=rnd.choice(("beye", "beye", "light", "fung"))))
    for back in (1, 0):                                                            # back rank first, a touch darker
        for i, sp in enumerate(specs):
            if sp["back"] != back:
                continue
            if anim == "cheer":
                up = (2 if (i + f) % 2 else 0) * sp["sz"]
                arms = (1,) if (i + f) % 3 == 0 else ()
            else:                                                                  # erupt: everybody up, arms and mugs high
                up = (4 if (i + f) % 2 else 2) * sp["sz"]
                arms = (-1, 1)
            hx = sp["x"]
            base = G - (3 * s if back else 0)
            heads.append((critter(c, sp["kind"], hx, base, sp["sz"], up, arms, anim == "erupt" or (i % 4 == 0), back), sp))
    g = c.finish()
    # warm rim light from the lanterns along the tops of heads, and eye glints
    for (x, y), t in list(g.items()):
        if t[0] == "crowd" and (x, y - 1) not in g and (x, y - 2) not in g:
            pass
    for (x, y), t in list(g.items()):
        if t == ("o",) and (x, y + 1) in g and g[(x, y + 1)][0] == "crowd" and (x, y - 1) not in g and hsh(x, y, 4) < 0.55:
            g[(x, y + 1)] = ("warm", 2)
    for (hx, hy, hr, kind), sp in heads:
        ey = int(round(hy + (0 if kind not in ("toad", "frog") else -1)))
        for dx in (-hr * 0.4, hr * 0.4):
            q = (int(round(hx + dx)), ey)
            if q in g and g[q][0] == "crowd":
                g[q] = (sp["eyec"], 1)
    return g


if __name__ == "__main__":
    write("badger", 96, 52, {"idle": [badger("idle", f) for f in range(3)],
                             "slide_coins": [badger("slide", f) for f in range(4)]}, {"anchor": [26, 51]})
    write("druid", 48, 72, {"idle": [druid("idle", f) for f in range(3)],
                            "summon": [druid("summon", f) for f in range(5)]}, {"anchor": [22, 71]})
    write("ring_light", 96, 48, {"glow": [ring_light(f) for f in range(5)]}, {"anchor": [48, 42]})
    write("chair", 28, 28, {"intact": [chair(0)], "smash": [chair(f) for f in (1, 2, 3)]}, {"anchor": [14, 27]})
    write("mug", 16, 16, {"intact": [mug(0)], "smash": [mug(f) for f in (1, 2, 3)]}, {"anchor": [7, 15]})
    write("crowd_front", 225, 44, {a: [crowd(225, 44, 1.7, 11, a, f, 5) for f in range(2)] for a in ("cheer", "erupt")},
          {"anchor": [112, 43]})
    write("crowd_gallery", 194, 24, {a: [crowd(194, 24, 0.9, 15, a, f, 9) for f in range(2)] for a in ("cheer", "erupt")},
          {"anchor": [97, 23]})
