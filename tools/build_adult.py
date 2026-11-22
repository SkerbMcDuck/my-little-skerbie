# Builds the adult Skerbie forms (64x64) as pixel grids -> JSON.
# Usage: python tools/build_adult.py stalker   (only the Shadow Stalker look test so far)
#        python tools/render.py art/source/skerbie/adult_stalker.json --out art/out/skerbie/adult_stalker
#
# Same angular house style as the approved baby and kids: straight-edged polygons,
# flat faceted shading lit from the top-left, the narrowed one-eye glare and one fang.
# Adult body plan: an upright humanoid animal on digitigrade legs.
#   stalker (SKB-AD-SPD, Shadow Stalker): lean and agile, a hooded cowl (the Speed
#   kid's slate scarf grown into a hood), swept-back ears through the hood, a long
#   tail ending in a blade. His constant smoke trail is a separate effect sprite.
# Arms and legs are built from joints (shoulder/elbow/paw, hip/knee/heel/toe) so the
# full animation set can pose them later; this file starts with idle + blink.
import json, math, sys

FORM = sys.argv[1] if len(sys.argv) > 1 else "stalker"
assert FORM == "stalker", "only the Shadow Stalker exists so far"

W = H = 64
PAL = {
    "o": "#0f0d14",
    "1": "#4a4552", "2": "#2a2630", "3": "#1a1720", "4": "#0b0a0e",   # main fur
    "5": "#8a8494", "6": "#615b6b", "7": "#433e4c", "8": "#2c2833",   # accent fur
    "e": "#ff9a8a", "E": "#ff3d3d", "f": "#b81f2e", "F": "#6e0f1c",   # eye glow
    "w": "#c9cfd6",                                                   # fang, blade edge (never dyed)
    "i": "#5a5e66",                                                   # blade iron (never dyed)
    "j": "#4d5e7a", "k": "#3b4a63", "l": "#2a3448",                   # hood/cowl, slate (never dyed)
}
LX, LY = -0.6, -0.8  # light from top-left
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
FUR, ACC, CLOTH, BLADE = "1234", "5678", "jkll", "wwii"

REST = {
    "arm":  {"sh": (33, 23), "el": (35, 32.5), "paw": (41.5, 37)},
    "farm": {"sh": (36.5, 22), "el": (39.5, 31), "paw": (45, 35)},
    "leg":  {"hip": (27, 38), "knee": (32, 47.5), "heel": (26, 56), "toe": (34.5, 62)},
    "fleg": {"hip": (31, 37.5), "knee": (36.5, 47), "heel": (31, 55.5), "toe": (39, 62)},
}
EYES = {
    "open":   ["ooo...", "eEEoo.", "EEEEEo", ".ffffF"],
    "half":   ["ooo...", "oooooo", "EEEEEo", ".ffffF"],
    "closed": ["ooo...", "222...", "oooooo", ".2222."],
}


def inside(poly, x, y):
    px, py, hit = x + .5, y + .5, False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[i - 1]
        if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


def poly_pts(poly):
    # poly may be one polygon or a list of them (a whole limb), shaded as one piece.
    polys = poly if isinstance(poly[0][0], (list, tuple)) else [poly]
    xs = [p[0] for q in polys for p in q]
    ys = [p[1] for q in polys for p in q]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    hw, hh = max(1, (max(xs) - min(xs)) / 2), max(1, (max(ys) - min(ys)) / 2)
    return {(x, y): ((x + .5 - cx) / hw, (y + .5 - cy) / hh)
            for y in range(-4, H + 2) for x in range(-2, W + 2) if any(inside(q, x, y) for q in polys)}


def tone(n, dark=0):
    lit = n[0] * LX + n[1] * LY
    t = 0 if lit > 0.5 else 1 if lit > -0.15 else 2 if lit > -0.55 else 3
    return min(3, t + dark)


def mv(poly, dx=0, dy=0):
    return [(x + dx, y + dy) for x, y in poly]


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def seg(a, b, wa, wb, ext=0.6):
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dy) or 1
    ux, uy = dx / ln, dy / ln
    nx, ny = -uy, ux
    a2, b2 = (a[0] - ux * ext, a[1] - uy * ext), (b[0] + ux * ext, b[1] + uy * ext)
    return [(a2[0] + nx * wa / 2, a2[1] + ny * wa / 2), (b2[0] + nx * wb / 2, b2[1] + ny * wb / 2),
            (b2[0] - nx * wb / 2, b2[1] - ny * wb / 2), (a2[0] - nx * wa / 2, a2[1] - ny * wa / 2)]


def frame(bob=0, ear=0, tail=0, cowl=0, eyes="open"):
    g, layer, order = {}, {}, {}
    z = [0]

    def paint(poly, part, ramp=FUR, dark=0, acc=None):
        z[0] += 1
        for p, n in poly_pts(poly).items():
            t = tone(n, dark)
            r = acc(p) if acc else False
            g[p] = (ACC if r is True else r if r else ramp)[t]
            layer[p], order[p] = part, z[0]

    b = bob
    up = (0, b)

    def arm(rest, part, dark=0):
        sh, el, pw = add(rest["sh"], up), add(rest["el"], up), add(rest["paw"], up)
        d = math.hypot(pw[0] - el[0], pw[1] - el[1]) or 1
        tip = (pw[0] + (pw[0] - el[0]) / d * 3, pw[1] + (pw[1] - el[1]) / d * 3)
        paint([seg(sh, el, 6, 4.6), seg(el, pw, 4.6, 3.8), seg(pw, tip, 5, 3.6, 0.4)], part, dark=dark)

    def leg(rest, part, dark=0):
        hip, kn = add(rest["hip"], up), rest["knee"]
        ball = (rest["toe"][0] - 3, rest["toe"][1] - 1)
        paint([seg(hip, kn, 8, 5.5),                       # thigh
               seg(kn, rest["heel"], 5, 4),                # shin, angled back
               seg(rest["heel"], ball, 4.4, 3.6, 0.8),     # long foot down to the ball
               seg(ball, rest["toe"], 3.6, 2.8, 0.6)],     # toes flat on the ground
              part, dark=dark)

    # Far side, one shade darker.
    paint(mv([(36, 7.5), (43, 3.5), (30.5 + ear, -0.5 + ear * 0.5)], 0, b), "far", dark=1)   # far ear
    arm(REST["farm"], "far", dark=1)
    leg(REST["fleg"], "far", dark=1)
    # Long tail: back from the rump in two bends, ending in a blade.
    t = tail
    knots = [(24, 41), (16, 45.5), (9.5, 41.5), (7 + t * 0.5, 33), (7 + t, 26)]
    widths = [5.5, 4.6, 4, 3.4, 3]
    paint([seg(mv([knots[i]], 0, b)[0], mv([knots[i + 1]], 0, b)[0], widths[i], widths[i + 1])
           for i in range(len(knots) - 1)], "tail")
    # The blade: a leaf-shaped iron tip with a bright edge on the lit side.
    paint(mv([(4 + t, 28), (10 + t, 27), (9.5 + t, 20), (7 + t, 12), (4 + t, 19)], 0, b), "blade", BLADE)
    # Cowl tail: the hood's cloth drapes down his back in tattered points.
    c = cowl
    paint(mv([(27, 19), (33, 17), (31, 27), (27, 34 + c), (25, 30 + c), (22, 35 + c * 1.5), (21, 28 + c),
              (18, 30 + c * 1.5), (21, 22)], 0, b), "cowl", CLOTH)
    # Torso: upright, a little hunched forward; deep chest, narrow waist.
    paint(mv([(22, 40), (22.5, 30), (25, 22), (31, 18.5), (37.5, 19.5), (40, 25), (38, 33), (34, 40), (28, 42.5)], 0, b),
          "body", acc=lambda p: inside(mv([(36, 21), (40, 25), (38, 33), (35, 37), (34.5, 26)], 0, b), *p))
    # Near leg.
    leg(REST["leg"], "leg")
    # Neck.
    paint(mv([(32, 14), (38, 13), (39.5, 20), (32.5, 22)], 0, b), "body")
    # Head: the family wedge, long snout.
    paint(mv([(33, 11), (36, 6.5), (42, 5), (47, 7), (55, 11.5), (53.5, 15), (46, 18), (37, 18), (34, 15.5)], 0, b),
          "head", acc=lambda p: p[1] >= 16.5 + b and 38 <= p[0] <= 49)
    # Hood over the back of the head and the shoulders, leaving the face clear.
    paint(mv([(29, 16), (31, 8), (36, 3.5), (41, 3), (44, 5.5), (40.5, 6.5), (37.5, 9), (36, 14), (38, 19),
              (34, 23), (27.5, 24), (26, 20)], 0, b), "hood", CLOTH)
    # Near ear: long and swept back, poking out through the hood.
    paint(mv([(33.5, 9), (43, 3.5), (28.5 + ear, -0.5 + ear * 0.5)], 0, b), "ear",
          acc=lambda p: inside(mv([(35.5, 7), (40.5, 4.2), (31.5 + ear, 1.2 + ear * 0.4)], 0, b), *p))
    # Near arm, outlined so it reads over his body.
    arm(REST["arm"], "arm")

    # Seams: darken the edge of a part where it sits on an earlier part.
    for (x, y), part in list(layer.items()):
        if part == "far":
            continue
        for dx, dy in N4:
            q = (x + dx, y + dy)
            if q in layer and layer[q] != part and order[q] < order[(x, y)] and (layer[q] != "far" or part == "arm"):
                g[(x, y)] = ("o" if part == "arm" else CLOTH[3] if part in ("hood", "cowl")
                             else BLADE[3] if part == "blade" else FUR[3])
                break
    for p in [p for p in g if not any((p[0] + dx, p[1] + dy) in g for dx, dy in N4)]:
        del g[p]
    filled = set(g)
    for (x, y) in filled:
        if any((x + dx, y + dy) not in filled for dx, dy in N4):
            g[(x, y)] = "o"

    # Eye (side view: the near eye only), mouth line and fang.
    for j, row in enumerate(EYES[eyes]):
        for i, ch in enumerate(row):
            if ch != ".":
                g[(41 + i, 9 + b + j)] = ch
    for x in range(47, 55):
        g[(x, 15 + b)] = "o"
    g[(48, 16 + b)] = "w"

    rows = ["".join(g.get((x, y), ".") for x in range(W)) for y in range(H)]
    pw, el = add(REST["arm"]["paw"], up), add(REST["arm"]["el"], up)
    aim = round(math.degrees(math.atan2(pw[1] - el[1], pw[0] - el[0])))
    attach = {"head": [41, 3 + b], "hand": [round(pw[0] + 1.5), round(pw[1] + 1)], "aim": aim,
              "torso": [31, 30 + b], "root_dx": 0}
    return rows, attach


A = {
    # Idle: breathe, ears twitch, the cowl and tail blade trail a frame behind.
    "idle": [frame(), frame(bob=-1), frame(bob=-1, ear=1, cowl=-1, tail=-1), frame(ear=1, cowl=-1, tail=-1)],
    "blink": [frame(eyes="half"), frame(eyes="closed")],
}
data = {
    "width": W, "height": H, "fps": 10, "palette": PAL,
    "dye_zones": {"main_fur": ["1", "2", "3", "4"], "accent_fur": ["5", "6", "7", "8"],
                  "eye_glow": ["e", "E", "f", "F"], "smoke": ["s", "S", "t", "T"]},
    "attach": {k: [a for _, a in v] for k, v in A.items()},
    "animations": {k: [r for r, _ in v] for k, v in A.items()},
}
json.dump(data, open(f"art/source/skerbie/adult_{FORM}.json", "w"), indent=1)
print("animations:", ", ".join(f"{k}[{len(v)}]" for k, v in A.items()))
