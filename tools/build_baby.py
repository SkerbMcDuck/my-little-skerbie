# Builds the baby Skerbie (32x32) idle + blink frames as pixel grids -> JSON.
# Angular, aggressive look (George, 2026-11-21): sharp shapes built from
# polygons, a low crouch with raised hackles, narrowed glaring eyes and a fang.
# Run: python tools/build_baby.py, then python tools/render.py art/source/skerbie/baby.json --out art/out/skerbie/baby
import json

W = H = 32
PAL = {
    "o": "#0f0d14",
    "1": "#4a4552", "2": "#2a2630", "3": "#1a1720", "4": "#0b0a0e",   # main fur
    "5": "#8a8494", "6": "#615b6b", "7": "#433e4c", "8": "#2c2833",   # accent fur
    "e": "#ff9a8a", "E": "#ff3d3d", "f": "#b81f2e", "F": "#6e0f1c",   # eye glow
    "w": "#c9cfd6",                                                   # fang (never dyed)
}
LX, LY = -0.6, -0.8  # light from top-left


def inside(poly, x, y):
    # Even-odd point-in-polygon test at the pixel centre.
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
    # Straight-line thresholds give flat, faceted planes instead of round shading.
    lit = n[0] * LX + n[1] * LY
    t = 1 if lit > 0.5 else 2 if lit > -0.15 else 3 if lit > -0.55 else 4
    return min(4, t + dark)


def mv(poly, dy):
    return [(x, y + dy) for x, y in poly]


def frame(bob=0, ear=0, tail=0, eyes="open"):
    g, layer = {}, {}

    def paint(poly, part, dark=0, acc=None):
        for p, n in poly_pts(poly).items():
            t = tone(n, dark)
            g[p] = str(t + 4) if (acc and acc(p)) else str(t)
            layer[p] = part

    b = bob
    # Far side, drawn first and one shade darker.
    paint(mv([(11.5, 12.5), (17.5, 11), (11.5 + ear * 0.5, 1.5)], b), "farear", dark=1)
    paint([(10, 21 + b), (14.5, 21 + b), (14, 26), (14, 29.5), (11.5, 29.5), (11.5, 25)], "farleg", dark=1)
    paint([(20, 20 + b), (24, 20 + b), (24, 29.5), (21.5, 29.5), (21, 24)], "farleg", dark=1)
    # Stub tail, a short spike flicking up and back.
    paint([(4.5, 15 + b), (7.5, 17 + b), (6, 20 + b), (2.5, 19 + b), (0.5, 11.5 + tail)], "tail",
          acc=lambda p: p[1] <= 14 + tail)
    # Hunched, wedge-shaped body: high shoulders, low haunch.
    paint([(4, 19 + b), (10, 15 + b), (17, 14 + b), (21, 18 + b), (20, 24), (9, 24), (4, 22)], "body",
          acc=lambda p: p[1] >= 22 and 11 <= p[0] <= 18)
    # Raised hackles: a sawtooth ridge of accent fur along the back.
    for x0, top in ((7, 12), (10.5, 10.5), (14, 11)):
        paint(mv([(x0, 17), (x0 + 1.5, top), (x0 + 4, 16)], b), "hackle", acc=lambda p: True)
    # Near legs: angled haunch at the back, straight braced foreleg.
    paint([(5.5, 21 + b), (11, 21 + b), (10, 26), (9.5, 29.5), (6.5, 29.5), (7.5, 25)], "leg")
    paint([(16.5, 20 + b), (20.5, 20 + b), (20, 29.5), (17.5, 29.5), (17.5, 24)], "leg")
    # Lowered, forward head with a long pointed snout.
    paint(mv([(14, 15), (16, 11), (21, 9), (25, 11), (30.5, 14.5), (29, 17), (23, 19.5), (17, 19.5)], b), "head",
          acc=lambda p: p[1] >= 18 + b and 17 <= p[0] <= 26)
    # Near ear: tall, sharp, swept back.
    paint(mv([(16, 11.5), (23, 10), (16.5 - ear, 0)], b), "ear",
          acc=lambda p: inside(mv([(17.8, 10.5), (21, 10), (17.4 - ear, 3)], b), *p))

    # Dark seams where parts overlap, so they read as separate shapes.
    for (x, y), part in list(layer.items()):
        below, left = layer.get((x, y + 1)), layer.get((x - 1, y))
        if part == "head" and below in ("body", "leg", "farleg"):
            g[(x, y)] = "4"
        if part == "leg" and (left == "farleg" or layer.get((x + 1, y)) == "farleg") and y > 24:
            g[(x, y)] = "4"
        if part == "ear" and left == "farear":
            g[(x, y)] = "4"

    # Drop orphan pixels (no filled neighbour on any side).
    for p in [p for p in g if not any((p[0] + dx, p[1] + dy) in g
                                      for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]:
        del g[p]
    filled = set(g)
    for (x, y) in filled:
        if any((x + dx, y + dy) not in filled for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            g[(x, y)] = "o"

    # Narrowed, glaring eyes: the brow slopes down toward the snout.
    ex, ey = 20, 12 + b
    near = {"open":   ["oo...", "eEoo.", "EEEEo", ".fffF"],
            "half":   ["oo...", "ooooo", "EEEEo", ".fffF"],
            "closed": ["oo...", "22...", "ooooo", ".222."]}[eyes]
    far = {"open": ["o.", "Eo", "fF"], "half": ["o.", "oo", "fF"], "closed": ["o.", "2.", "oo"]}[eyes]
    for j, row in enumerate(near):
        for i, c in enumerate(row):
            if c != ".":
                g[(ex + i, ey + j)] = c
    for j, row in enumerate(far):
        for i, c in enumerate(row):
            if c != ".":
                g[(26 + i, ey + 1 + j)] = c
    # Mouth line and a single fang.
    for x in range(24, 29):
        g[(x, 16 + b)] = "o"
    g[(25, 17 + b)] = "w"
    return ["".join(g.get((x, y), ".") for x in range(W)) for y in range(H)]


# Idle: breathe (1 px bob), ears twitch and the tail flicks one frame behind.
idle = [frame(), frame(bob=-1), frame(bob=-1, ear=1), frame(ear=1, tail=-1)]
blink = [frame(eyes="half"), frame(eyes="closed")]

data = {
    "width": W, "height": H, "fps": 10, "palette": PAL,
    "dye_zones": {"main_fur": ["1", "2", "3", "4"], "accent_fur": ["5", "6", "7", "8"],
                  "eye_glow": ["e", "E", "f", "F"], "smoke": ["s", "S", "t", "T"]},
    "attach": {},
    "animations": {"idle": idle, "blink": blink},
}
json.dump(data, open("art/source/skerbie/baby.json", "w"), indent=1)
print("\n".join(idle[0]))
