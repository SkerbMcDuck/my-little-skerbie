# Builds the Speed kid Skerbie (48x48) look test: idle [4] + blink [2] -> JSON.
# Same angular house style as the approved baby (straight-edged polygons, flat
# faceted shading, narrowed glaring eyes, one fang). Kid body plan: crouched and
# half-upright on bent hind legs, forepaws held up. Speed kid: sleek and lean,
# swept-back ears, a long thin tail and a tattered scarf trailing behind.
# Run: python tools/build_kid_speed.py, then
#      python tools/render.py art/source/skerbie/kid_speed.json --out art/out/skerbie/kid_speed
import json

W = H = 48
PAL = {
    "o": "#0f0d14",
    "1": "#4a4552", "2": "#2a2630", "3": "#1a1720", "4": "#0b0a0e",   # main fur
    "5": "#8a8494", "6": "#615b6b", "7": "#433e4c", "8": "#2c2833",   # accent fur
    "e": "#ff9a8a", "E": "#ff3d3d", "f": "#b81f2e", "F": "#6e0f1c",   # eye glow
    "w": "#c9cfd6",                                                   # fang (never dyed)
    "j": "#4d5e7a", "k": "#3b4a63", "l": "#2a3448",                   # scarf, slate blue (never dyed)
}
LX, LY = -0.6, -0.8  # light from top-left
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
FUR, ACC, SCARF = "1234", "5678", "jkll"


def inside(poly, x, y):
    px, py, hit = x + .5, y + .5, False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[i - 1]
        if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


def poly_pts(poly):
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    hw, hh = max(1, (max(xs) - min(xs)) / 2), max(1, (max(ys) - min(ys)) / 2)
    return {(x, y): ((x + .5 - cx) / hw, (y + .5 - cy) / hh)
            for y in range(H) for x in range(W) if inside(poly, x, y)}


def tone(n, dark=0):
    lit = n[0] * LX + n[1] * LY
    t = 0 if lit > 0.5 else 1 if lit > -0.15 else 2 if lit > -0.55 else 3
    return min(3, t + dark)


def mv(poly, dx=0, dy=0):
    return [(x + dx, y + dy) for x, y in poly]


def frame(bob=0, ear=0, tail=0, scarf=0, eyes="open"):
    g, layer, order = {}, {}, {}
    z = [0]

    def paint(poly, part, ramp=FUR, dark=0, acc=None):
        z[0] += 1
        for p, n in poly_pts(poly).items():
            t = tone(n, dark)
            g[p] = (ACC if acc and acc(p) else ramp)[t]
            layer[p], order[p] = part, z[0]

    b = bob
    # Far side, one shade darker (offset a little right and up from the near side).
    paint(mv([(28, 9), (35, 6.5), (21.5 + ear, 0.5 + ear * 0.5)], 0, b), "far", dark=1)
    paint(mv([(28, 17), (33, 17.5), (34, 24), (30, 25)], 0, b), "far", dark=1)
    paint(mv([(30, 22), (34, 22), (39, 26), (36, 29)], 0, b), "far", dark=1)
    paint([(17, 28 + b), (27, 27 + b), (30, 36), (24, 39.5), (18, 35)], "far", dark=1)
    paint([(25, 34.5), (30, 37), (23, 43.5), (19.5, 42)], "far", dark=1)
    paint([(18.5, 41.5), (22.5, 41), (31, 45.5), (30.5, 46.5), (21, 46.5)], "far", dark=1)
    # Long thin tail in one piece: back from the rump, then curling up.
    t = tail
    paint(mv([(14, 29), (16, 33.5), (9, 36), (4, 33), (1.5 + t, 26), (1 + t, 19), (3.5 + t, 20),
              (4.5 + t * 0.5, 27), (7, 31.5), (11, 31.5)], 0, b), "tail",
          acc=lambda p: p[1] <= 23 + b)
    # Tattered scarf streaming back from the neck.
    s = scarf
    paint(mv([(22, 14), (25, 18), (18, 20), (12, 22 + s), (13, 19.5 + s), (7, 20 + s),
              (10, 17.5 + s * 0.5), (5, 16 + s * 0.5), (13, 14.5)], 0, b), "scarf", SCARF)
    # Torso: angled forward, deep chest, narrow waist.
    paint(mv([(13, 30), (16, 22), (21, 16), (29, 14), (33, 18), (32, 25), (27, 31), (23, 36), (14, 36)], 0, b),
          "body", acc=lambda p: inside(mv([(30, 16), (33, 18), (32, 25), (28, 30), (27.5, 21)], 0, b), *p))
    # Two hackle spikes on the upper back.
    paint(mv([(18, 20), (18, 13.5), (23, 17)], 0, b), "body", acc=lambda p: True)
    paint(mv([(14, 25), (12, 19), (18, 22)], 0, b), "body", acc=lambda p: True)
    # Near hind leg: big thigh, shin, long foot (digitigrade crouch). Feet stay planted.
    paint([(11, 28 + b), (22, 27 + b), (26, 37), (20, 40), (13, 35)], "leg")
    # Shin angles back down to a raised heel, then the long foot runs forward.
    paint([(20, 34.5), (26, 37), (18.5, 43.5), (15, 42)], "leg")
    paint([(14, 41.5), (18, 41), (27, 45.5), (26.5, 46.5), (16.5, 46.5)], "leg")
    # Scarf wrap around the neck.
    paint(mv([(22, 13.5), (30, 11.5), (32, 16), (24, 18.5)], 0, b), "wrap", SCARF)
    # Head: the baby's wedge, longer and sleeker.
    paint(mv([(26, 10), (28.5, 5), (34, 3), (39, 5), (46.5, 10), (45, 13), (38, 15.5), (30, 15.5), (27, 13.5)], 0, b),
          "head", acc=lambda p: p[1] >= 14 + b and 31 <= p[0] <= 41)
    # Near ear: long, wide at the base, swept far back.
    paint(mv([(28, 8.5), (36, 5), (24 + ear, 0 + ear * 0.5)], 0, b), "ear",
          acc=lambda p: inside(mv([(29.8, 7.4), (33.5, 6), (26 + ear, 2.5 + ear * 0.4)], 0, b), *p))
    # Near arm, held up and forward, ready.
    paint(mv([(25, 17), (30, 17.5), (31, 25), (26.5, 26)], 0, b), "arm")
    paint(mv([(27, 22), (31, 22), (37, 27), (34, 30)], 0, b), "arm")
    paint(mv([(33, 26), (37.5, 25.5), (39, 29), (34.5, 31)], 0, b), "arm")

    # Seams: where a part sits on top of a different part, darken its edge pixel.
    for (x, y), part in list(layer.items()):
        if part in ("far",):
            continue
        for dx, dy in N4:
            q = (x + dx, y + dy)
            if q in layer and layer[q] != part and order[q] < order[(x, y)] and layer[q] != "far":
                g[(x, y)] = SCARF[3] if part in ("scarf", "wrap") else FUR[3]
                break
    for p in [p for p in g if not any((p[0] + dx, p[1] + dy) in g for dx, dy in N4)]:
        del g[p]
    filled = set(g)
    for (x, y) in filled:
        if any((x + dx, y + dy) not in filled for dx, dy in N4):
            g[(x, y)] = "o"

    # Eyes: narrowed glare, brow sloping down toward the snout.
    near = {"open":   ["ooo...", "eEEoo.", "EEEEEo", ".ffffF"],
            "half":   ["ooo...", "oooooo", "EEEEEo", ".ffffF"],
            "closed": ["ooo...", "222...", "oooooo", ".2222."]}[eyes]
    far = {"open": ["o.", "Eo", "fF"], "half": ["o.", "oo", "fF"], "closed": ["o.", "2.", "oo"]}[eyes]
    for j, row in enumerate(near):
        for i, ch in enumerate(row):
            if ch != ".":
                g[(33 + i, 7 + b + j)] = ch
    for j, row in enumerate(far):
        for i, ch in enumerate(row):
            if ch != ".":
                g[(41 + i, 8 + b + j)] = ch
    for x in range(39, 46):
        g[(x, 13 + b)] = "o"
    g[(40, 14 + b)] = "w"
    rows = ["".join(g.get((x, y), ".") for x in range(W)) for y in range(H)]
    attach = {"head": [34, 2 + b], "hand": [36, 28 + b], "torso": [24, 24 + b]}
    return rows, attach


A = {
    # Idle: breathe, ears twitch, the scarf and tail trail one frame behind.
    "idle": [frame(), frame(bob=-1), frame(bob=-1, ear=1, scarf=-1, tail=-1), frame(ear=1, scarf=-1, tail=-1)],
    "blink": [frame(eyes="half"), frame(eyes="closed")],
}
data = {
    "width": W, "height": H, "fps": 10, "palette": PAL,
    "dye_zones": {"main_fur": ["1", "2", "3", "4"], "accent_fur": ["5", "6", "7", "8"],
                  "eye_glow": ["e", "E", "f", "F"], "smoke": ["s", "S", "t", "T"]},
    "attach": {k: [a for _, a in v] for k, v in A.items()},
    "animations": {k: [r for r, _ in v] for k, v in A.items()},
}
json.dump(data, open("art/source/skerbie/kid_speed.json", "w"), indent=1)
print("\n".join(A["idle"][0][0]))
