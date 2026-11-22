# Builds the adult Skerbie forms (64x64), all 37 animations, as pixel grids -> JSON.
# Usage: python tools/build_adult.py stalker|juggernaut [--look]   (--look: idle + blink only)
#        python tools/render.py art/source/skerbie/adult_stalker.json --out art/out/skerbie/adult_stalker
#
# Same angular house style as the approved baby and kids: straight-edged polygons,
# flat faceted shading lit from the top-left, the narrowed one-eye glare and one fang.
# Adult body plan: an upright humanoid animal on digitigrade legs.
#   stalker (SKB-AD-SPD, Shadow Stalker): lean and agile, a hooded cowl (the Speed
#   kid's slate scarf grown into a hood), swept-back ears through the hood, a long
#   tail ending in a blade. His constant smoke trail is a separate effect sprite.
# Look approved by George (2026-11-22). frame(...) is a rig: arms and legs are built
# from joints (shoulder/elbow/paw, hip/knee/heel/toe), each limb shaded as one piece,
# and with no pose set idle and blink come out exactly as approved. The animation
# choreography follows the kids' (tools/build_kid.py), scaled to the bigger body.
import json, math, sys

FORMS = ("stalker", "juggernaut")
FORM = sys.argv[1] if len(sys.argv) > 1 else "stalker"
assert FORM in FORMS, f"form must be one of {FORMS}"
JUG = FORM == "juggernaut"
#   juggernaut (SKB-AD-STR): upright and hulking, a heavy grounded stance, massive
#   forearms in worn cloth wraps (the Strength kid's wraps grown up), a shaggy grey mane
#   and scarred grey fur (both accent zone), short spiked tail.

W = H = 64
PAL = {
    "o": "#0f0d14",
    "1": "#4a4552", "2": "#2a2630", "3": "#1a1720", "4": "#0b0a0e",   # main fur
    "5": "#8a8494", "6": "#615b6b", "7": "#433e4c", "8": "#2c2833",   # accent fur
    "e": "#ff9a8a", "E": "#ff3d3d", "f": "#b81f2e", "F": "#6e0f1c",   # eye glow
    "w": "#c9cfd6",                                                   # fang, blade edge (never dyed)
}
if FORM == "stalker":
    PAL.update({"i": "#5a5e66",                                       # blade iron (never dyed)
                "j": "#4d5e7a", "k": "#3b4a63", "l": "#2a3448"})      # hood/cowl, slate (never dyed)
if JUG:
    PAL.update({"q": "#bfae8c", "r": "#a8945e", "u": "#8b7a4a"})      # forearm wraps, worn cloth (never dyed)
LX, LY = -0.6, -0.8  # light from top-left
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
FUR, ACC, CLOTH, BLADE, WRAP = "1234", "5678", "jkll", "wwii", "qruu"

REST = {
    "arm":  {"sh": (33, 23), "el": (35, 32.5), "paw": (41.5, 37)},
    "farm": {"sh": (36.5, 22), "el": (39.5, 31), "paw": (45, 35)},
    "leg":  {"hip": (27, 38), "knee": (32, 47.5), "heel": (26, 56), "toe": (34.5, 62)},
    "fleg": {"hip": (31, 37.5), "knee": (36.5, 47), "heel": (31, 55.5), "toe": (39, 62)},
}
# Limb thickness: arm (upper, elbow, wrist, paw a, paw b), leg (thigh top, knee, shin end, foot).
ARM_W = (6, 4.6, 3.8, 5, 3.6)
LEG_W = (8, 5.5, 5, 4, 4.4, 3.6, 2.8)
if JUG:  # wider stance, shoulders set forward, huge forearms that widen toward the fist
    REST = {
        # Long, heavy forearms hanging forward, fists down by the thighs.
        "arm":  {"sh": (33, 22), "el": (35.5, 31.5), "paw": (40.5, 43.5)},
        "farm": {"sh": (38, 21), "el": (42, 30), "paw": (48, 37.5)},
        "leg":  {"hip": (25.5, 39), "knee": (30, 48.5), "heel": (24, 56), "toe": (33.5, 62)},
        "fleg": {"hip": (32, 38.5), "knee": (37.5, 48), "heel": (32.5, 55.5), "toe": (41, 62)},
    }
    ARM_W = (8.5, 6.5, 9, 8, 6.5)
    LEG_W = (11, 7.5, 6.5, 5.5, 5.6, 4.6, 3.6)
EYES = {  # '.' leaves the fur underneath
    "open":   ["ooo...", "eEEoo.", "EEEEEo", ".ffffF"],
    "half":   ["ooo...", "oooooo", "EEEEEo", ".ffffF"],
    "closed": ["ooo...", "222...", "oooooo", ".2222."],
    "happy":  ["ooo...", "ooeEEo", "Ef..fE", "o....o"],   # glowing smug squint
    "wide":   ["oo....", "eEEoo.", "EEEEEo", "fffffF"],
    "ko":     ["fo.fo.", ".ffo..", ".ffo..", "fo.fo."],   # dim X
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


def frame(bob=0, crouch=0, lean=0, head=(0, 0), ear=0, tail=0, cowl=0, eyes="open", mouth="closed",
          arm=None, farm=None, leg=None, fleg=None, off=(0, 0)):
    """One pose, in pixels. bob: body up(-)/down(+) with feet planted. crouch: sink the hips,
    knees push forward. lean: tip the chest and head forward (+) or back (-). head: extra (dx, dy).
    ear: sweep ears back. tail / cowl: flick the tips. arm / farm: {"el"/"paw": nudge} or
    {"el_at"/"paw_at": exact pixel}. leg / fleg: {"knee"/"heel"/"toe": nudge}.
    off: (root_dx, dy); root_dx is not baked in, the game slides the sprite by it."""
    g, layer, order = {}, {}, {}
    z = [0]

    def paint(poly, part, ramp=FUR, dark=0, acc=None):
        z[0] += 1
        for p, n in poly_pts(poly).items():
            t = tone(n, dark)
            r = acc(p) if acc else False
            g[p] = (ACC if r is True else r if r else ramp)[t]
            layer[p], order[p] = part, z[0]

    by = bob + crouch
    up = (lean, by)                                 # chest and shoulders
    # Head offset in whole pixels (the eye and mouth are stamped on the grid; snout stays in frame).
    hx, hy = round(min(head[0], 1) + lean), round(head[1] + by)
    lift = hy + off[1]
    flat = max(0, ear - 1) * 0.6
    if lift + flat < -1:                            # head raised: pin ears back inside the frame
        ear, flat = ear + (-1 - lift - flat) * 0.8, -1 - lift
    e, fy = ear, flat

    def arm_joints(rest, pose):
        pose = pose or {}
        sh = add(rest["sh"], up)
        el = pose["el_at"] if "el_at" in pose else add(add(rest["el"], up), pose.get("el", (0, 0)))
        pw = pose["paw_at"] if "paw_at" in pose else add(add(rest["paw"], up), pose.get("paw", (0, 0)))
        floor = 57 - off[1]  # paws stay above the ground line
        if JUG and pw[0] > 55:  # his big fists stay inside the right edge
            pw = (55, pw[1])
        if pw[1] > floor:
            pw = (pw[0] + 1.5, floor)
        if el[1] > floor:
            el = (el[0], floor)
        return sh, el, pw

    def arm_paint(rest, pose, part, dark=0):
        sh, el, pw = arm_joints(rest, pose)
        d = math.hypot(pw[0] - el[0], pw[1] - el[1]) or 1
        tip = (pw[0] + (pw[0] - el[0]) / d * 3, pw[1] + (pw[1] - el[1]) / d * 3)
        wu, we, ww, pa, pb = ARM_W
        if JUG:  # fur upper arm and elbow, then cloth wraps from mid-forearm over the fist
            mid = (el[0] + (pw[0] - el[0]) * 0.72, el[1] + (pw[1] - el[1]) * 0.72)
            wide = we + (ww - we) * 0.72
            paint([seg(sh, el, wu, we), seg(el, mid, we, wide)], part, dark=dark)
            paint([seg(mid, pw, wide, ww, 0.2), seg(pw, tip, pa, pb, 0.4)], part, WRAP, dark=dark)
        else:
            paint([seg(sh, el, wu, we), seg(el, pw, we, ww), seg(pw, tip, pa, pb, 0.4)], part, dark=dark)

    def leg_paint(rest, pose, part, dark=0):
        pose = pose or {}
        hip = add(rest["hip"], (0, by))
        kn = add(add(rest["knee"], (crouch * 0.5, crouch * 0.5)), pose.get("knee", (0, 0)))
        heel = add(rest["heel"], pose.get("heel", (0, 0)))
        toe = add(rest["toe"], pose.get("toe", (0, 0)))
        ball = (toe[0] - 3, toe[1] - 1)
        t1, t2, s1, s2, f1, f2, f3 = LEG_W
        paint([seg(hip, kn, t1, t2),               # thigh
               seg(kn, heel, s1, s2),              # shin, angled back
               seg(heel, ball, f1, f2, 0.8),       # long foot down to the ball
               seg(ball, toe, f2, f3, 0.6)],       # toes flat on the ground
              part, dark=dark)

    # Far side, one shade darker.
    if JUG:  # short, thick ears set lower
        far_ear = [(35, 9), (42.5, 5.5), (33 + e, 0.5 + e * 0.5 + fy)]
    else:
        far_ear = [(36, 7.5), (43, 3.5), (30.5 + e, -0.5 + e * 0.5 + fy)]
    paint(mv(far_ear, hx, hy), "far", dark=1)
    arm_paint(REST["farm"], farm, "far", dark=1)
    leg_paint(REST["fleg"], fleg, "far", dark=1)
    t = tail
    if JUG:  # short, thick tail with a spiked accent-fur tip (kept inside the left edge)
        t = max(t, -2)
        paint(mv([(20, 39), (22.5, 46), (14, 50), (7, 48), (3 + t, 42), (5.5 + t, 39.5), (9, 43.5), (15, 43)], 0, by),
              "tail", acc=lambda p: p[0] <= 8 + t)
    else:
        # Long tail: back from the rump in two bends, ending in a blade.
        knots = [(24, 41), (16, 45.5), (9.5, 41.5), (7 + t * 0.5, 33), (7 + t, 26)]
        widths = [5.5, 4.6, 4, 3.4, 3]
        paint([seg(mv([knots[i]], 0, by)[0], mv([knots[i + 1]], 0, by)[0], widths[i], widths[i + 1])
               for i in range(len(knots) - 1)], "tail")
        # The blade: a leaf-shaped iron tip with a bright edge on the lit side.
        paint(mv([(4 + t, 28), (10 + t, 27), (9.5 + t, 20), (7 + t, 12), (4 + t, 19)], 0, by), "blade", BLADE)
        # Cowl tail: the hood's cloth drapes down his back in tattered points.
        c = cowl
        paint(mv([(27, 19), (33, 17), (31, 27), (27, 34 + c), (25, 30 + c), (22, 35 + c * 1.5), (21, 28 + c),
                  (18, 30 + c * 1.5), (21, 22)], *up), "cowl", CLOTH)
    # Torso: upright, a little hunched forward. The chest takes the lean, the hips stay.
    if JUG:  # a barrel chest and a broad back, hunched over a low centre of gravity
        torso = [(18, 42, 0), (17.5, 31, 0.5), (20, 21, 1), (28, 15.5, 1), (40, 16, 1), (44.5, 23, 1),
                 (43, 34, 0.5), (37, 42, 0), (27, 45, 0)]
        chest = mv([(39, 18), (44.5, 23), (43, 34), (39, 39), (37.5, 26)], *up)
    else:
        torso = [(22, 40, 0), (22.5, 30, 0.5), (25, 22, 1), (31, 18.5, 1), (37.5, 19.5, 1), (40, 25, 1),
                 (38, 33, 0.5), (34, 40, 0), (28, 42.5, 0)]
        chest = mv([(36, 21), (40, 25), (38, 33), (35, 37), (34.5, 26)], *up)
    paint([(x + lean * k, y + by) for x, y, k in torso], "body", acc=lambda p: inside(chest, *p))
    # Near leg.
    leg_paint(REST["leg"], leg, "leg")
    # Neck, halfway between chest and head.
    neck = [(31, 14), (39, 13), (41, 21), (31.5, 23)] if JUG else [(32, 14), (38, 13), (39.5, 20), (32.5, 22)]
    paint(mv(neck, (lean + hx) / 2, (by + hy) / 2), "body")
    if JUG:  # thick, shaggy grey mane over the shoulders, neck and upper back
        paint(mv([(17, 25), (13, 21), (18.5, 19.5), (16, 14), (22, 15), (22.5, 9), (27.5, 12), (30, 6.5),
                  (33, 10.5), (37.5, 8), (37, 13), (42, 13.5), (39.5, 18.5), (43.5, 21.5), (37.5, 22),
                  (33, 26), (29, 23.5), (23, 27.5), (21, 24)], (lean + hx) / 2, (by + hy) / 2),
              "mane", acc=lambda p: True)
    # Head: the family wedge, long snout.
    paint(mv([(33, 11), (36, 6.5), (42, 5), (47, 7), (55, 11.5), (53.5, 15), (46, 18), (37, 18), (34, 15.5)], hx, hy),
          "head", acc=lambda p: p[1] >= 16.5 + hy and 38 + hx <= p[0] <= 49 + hx)
    if not JUG:
        # Hood over the back of the head and the shoulders, leaving the face clear.
        paint(mv([(29, 16), (31, 8), (36, 3.5), (41, 3), (44, 5.5), (40.5, 6.5), (37.5, 9), (36, 14), (38, 19),
                  (34, 23), (27.5, 24), (26, 20)], hx, hy), "hood", CLOTH)
    if JUG:
        paint(mv([(34, 9.5), (42.5, 6), (31 + e, 0 + e * 0.5 + fy)], hx, hy), "ear",
              acc=lambda p: inside(mv([(35.8, 8.2), (40, 6.5), (33 + e, 2.2 + e * 0.4 + fy)], hx, hy), *p))
    else:
        # Near ear: long and swept back, poking out through the hood.
        paint(mv([(33.5, 9), (43, 3.5), (28.5 + e, -0.5 + e * 0.5 + fy)], hx, hy), "ear",
              acc=lambda p: inside(mv([(35.5, 7), (40.5, 4.2), (31.5 + e, 1.2 + e * 0.4 + fy)], hx, hy), *p))
    # Near arm, outlined so it reads over his body.
    arm_paint(REST["arm"], arm, "arm")
    if JUG:  # old scars: pale accent-fur slashes across his chest, thigh and snout
        scars = [mv([(x, y)], *up)[0] for x, y in ((38, 27), (39, 28), (40, 29), (41, 30), (36, 31), (37, 32))]
        scars += [(x, y + by) for x, y in ((23, 42), (24, 43), (25, 44))]
        scars += [mv([(x, y)], hx, hy)[0] for x, y in ((45, 8), (46, 9), (47, 10))]
        for x, y in scars:
            p = (round(x), round(y))
            if layer.get(p) in ("body", "leg", "head"):
                g[p] = ACC[0]

    # Seams: darken the edge of a part where it sits on an earlier part.
    for (x, y), part in list(layer.items()):
        if part == "far":
            continue
        for dx, dy in N4:
            q = (x + dx, y + dy)
            if q in layer and layer[q] != part and order[q] < order[(x, y)] and (layer[q] != "far" or part == "arm"):
                g[(x, y)] = ("o" if part == "arm" else CLOTH[3] if part in ("hood", "cowl")
                             else BLADE[3] if part == "blade" else ACC[3] if part == "mane" else FUR[3])
                break
    for p in [p for p in g if not any((p[0] + dx, p[1] + dy) in g for dx, dy in N4)]:
        del g[p]
    filled = set(g)
    for (x, y) in filled:
        if any((x + dx, y + dy) not in filled for dx, dy in N4):
            g[(x, y)] = "o"

    # Eye (side view: the near eye only), mouth and fang.
    for j, row in enumerate(EYES[eyes]):
        for i, ch in enumerate(row):
            if ch != ".":
                g[(41 + hx + i, 9 + hy + j)] = ch
    if mouth == "open":
        for x in range(46, 56):
            g[(x + hx, 15 + hy)] = "o"
        for x in range(46, 54):
            g[(x + hx, 16 + hy)] = "o"
    else:
        for x in range(47, 55):
            g[(x + hx, 15 + hy)] = "o"
    g[(48 + hx, 16 + hy)] = "w"

    ox, oy = off
    rows = ["".join(g.get((x, y - oy), ".") for x in range(W)) for y in range(H)]
    _, el, pw = arm_joints(REST["arm"], arm)
    d = math.hypot(pw[0] - el[0], pw[1] - el[1]) or 1
    grip = (pw[0] + (pw[0] - el[0]) / d * 1.5, pw[1] + (pw[1] - el[1]) / d * 1.5)
    aim = round(math.degrees(math.atan2(pw[1] - el[1], pw[0] - el[0])))
    attach = {"head": [41 + hx, 3 + hy + oy], "hand": [round(grip[0]), round(grip[1]) + oy], "aim": aim,
              "torso": [round(31 + lean * 0.5), 30 + by + oy], "root_dx": ox}
    return rows, attach


# ---- Animations ----
# F(...) takes the kids' choreography numbers and scales them to the adult body
# (about 4/3). Exact placements ("el_at"/"paw_at") are adult pixels and aren't scaled.
K = 4 / 3


def sc(v):
    return (round(v[0] * K, 1), round(v[1] * K, 1))


def F(**kw):
    for k in ("crouch", "lean"):
        if k in kw:
            kw[k] = round(kw[k] * K)
    if "head" in kw:
        kw["head"] = sc(kw["head"])
    if "off" in kw:
        kw["off"] = (round(kw["off"][0] * K), round(kw["off"][1] * K))
    for k in ("arm", "farm", "leg", "fleg"):
        if kw.get(k):
            kw[k] = {j: (v if j.endswith("_at") else sc(v)) for j, v in kw[k].items()}
    return frame(**kw)


A = {}


def anim(name, frames):
    A[name] = frames


# Exact arm placements for poses where the paw must clear his head (adult pixels).
UP_N = {"el_at": (33, 14), "paw_at": (35.5, 4.5)}     # near paw straight up over his ears
UP_F = {"el_at": (36.5, 13), "paw_at": (39.5, 4)}     # far paw up
BACK = {"el_at": (28, 16), "paw_at": (22.5, 9)}       # wound back behind his head
REACH = {"el_at": (39, 16), "paw_at": (45, 8)}        # reaching up and forward

# ---- Home ----
anim("idle", [frame(), frame(bob=-1), frame(bob=-1, ear=1, cowl=-1, tail=-1), frame(ear=1, cowl=-1, tail=-1)])
anim("blink", [frame(eyes="half"), frame(eyes="closed")])
STEP = [{"heel": (-3, 0), "toe": (-3, 0)}, {"knee": (1, -2), "heel": (-1, -3), "toe": (1, -2)},
        {"knee": (2, -1), "heel": (2, -1), "toe": (3, 0)}, {"heel": (3, 0), "toe": (3, 0)},
        {"heel": (1, 0), "toe": (1, 0)}, {"heel": (-1, 0), "toe": (-1, 0)}]
anim("walk", [F(bob=-1 if i in (1, 4) else 0, leg=STEP[i], fleg=STEP[(i + 3) % 6],
                arm={"el": (-1 + (i % 3), 0), "paw": (-2 + (i % 3) * 2, 0)},
                farm={"el": (1 - (i % 3), 0), "paw": (2 - (i % 3) * 2, 0)},
                cowl=-1 if i % 2 else 0, tail=-1 if i in (2, 5) else 0) for i in range(6)])
anim("happy", [
    F(crouch=2, eyes="happy"),
    F(off=(0, -3), eyes="happy", arm=REACH, cowl=-1, tail=-1),
    F(off=(0, -4), eyes="happy", arm=UP_N, farm=UP_F, cowl=-2, tail=-2,
      leg={"heel": (0, -1), "toe": (0, -1)}, fleg={"heel": (0, -1), "toe": (0, -1)}),
    F(off=(0, -1), eyes="happy", arm={"el": (0, -1), "paw": (0, -2)}),
])
anim("eat", [
    F(arm={"el": (1, -2), "paw": (2, -7)}, farm={"el": (1, -2), "paw": (2, -6)}, head=(0, 1)),
    F(arm={"el": (1, -2), "paw": (2, -8)}, farm={"el": (1, -2), "paw": (2, -7)}, head=(0, 1), mouth="open"),
    F(arm={"el": (1, -2), "paw": (2, -7)}, farm={"el": (1, -2), "paw": (2, -6)}, head=(0, 2)),
    F(arm={"el": (1, -2), "paw": (2, -8)}, farm={"el": (1, -2), "paw": (2, -7)}, head=(0, 1), mouth="open", tail=-1),
])
CURL = dict(crouch=4, lean=-1, head=(-1, 5), ear=3, tail=1, arm={"el": (-1, 2), "paw": (-6, -2)},
            farm={"el": (-1, 2), "paw": (-6, -2)})
anim("sleep", [F(**CURL, eyes="closed"), F(**CURL, eyes="closed", bob=1)])
anim("tired", [
    F(crouch=3, lean=2, head=(0, 2), ear=2, eyes="half", arm={"el": (0, 3), "paw": (-3, 6)}, tail=1),
    F(crouch=4, lean=2, head=(0, 3), ear=2, eyes="half", arm={"el": (0, 3), "paw": (-3, 7)}, tail=1),
])
anim("petted", [
    F(head=(-1, -1), lean=-1, eyes="happy", ear=2, tail=-1),
    F(head=(-1, -2), lean=-1, eyes="happy", ear=3, tail=-2, bob=-1),
    F(head=(-1, -1), lean=-1, eyes="happy", ear=2, tail=0),
])
KO = dict(crouch=9, lean=5, head=(0, 6), ear=3, eyes="ko", arm={"el": (0, 5), "paw": (-2, 9)},
          farm={"el": (0, 5), "paw": (-2, 9)}, tail=2)
anim("knocked_out", [
    F(lean=-2, head=(-1, 0), eyes="ko", ear=3, arm={"el": (-2, 2), "paw": (-5, 4)}),
    F(crouch=5, lean=2, head=(0, 3), eyes="ko", ear=3, arm={"el": (0, 3), "paw": (-2, 6)}),
    F(**KO),
])
anim("knocked_out_loop", [F(**KO), F(**{**KO, "ear": 2, "tail": 1})])
anim("working", [  # hammering; the hammer is a separate sprite on the hand point
    F(arm=BACK, ear=1),
    F(arm=UP_N, lean=-1, ear=1),
    F(crouch=1, lean=2, arm={"el": (1, -1), "paw": (4, 1)}, eyes="half"),
    F(arm={"el": (0, -2), "paw": (0, -4)}),
])
HUG = {"el": (1, 0), "paw": (0, -3)}
anim("carry", [F(bob=-1 if i % 2 else 0, arm=HUG, farm=HUG, head=(0, -1), leg=STEP[i * 3 // 2 % 6],
                 fleg=STEP[(i * 3 // 2 + 3) % 6], tail=-1 if i % 2 else 0) for i in range(4)])
anim("cheer", [
    F(crouch=2, eyes="wide", arm={"el": (0, 2), "paw": (-1, 2)}),
    F(lean=-2, eyes="wide", mouth="open", arm=REACH, farm={"el_at": (41, 15), "paw_at": (47, 7)}, tail=-2, cowl=-1),
    F(lean=-2, bob=-1, eyes="happy", mouth="open", arm=UP_N, farm=UP_F, tail=-3, cowl=-2),
    F(lean=-1, eyes="wide", arm={"el": (0, -3), "paw": (0, -6)}, tail=-1),
])
anim("catch", [
    F(crouch=2, head=(0, 1)),
    F(off=(0, -4), lean=-2, head=(0, -1), mouth="open", arm=REACH, farm={"el_at": (41, 15), "paw_at": (47, 7)},
      leg={"heel": (0, -1), "toe": (0, -1)}, cowl=-2, tail=-2),
    F(crouch=1, arm={"el": (1, -2), "paw": (1, -4)}),
])

# ---- Fights: claws ----
GUARD = {"el": (1, -1), "paw": (1, -3)}
anim("battle_stance", [F(crouch=2, lean=1, head=(0, 1), ear=2, arm=GUARD, tail=-1 - (i % 2),
                         bob=-1 if i in (1, 2) else 0, cowl=-1 if i in (2, 3) else 0) for i in range(4)])
anim("basic_attack", [
    F(off=(-1, 0), crouch=2, lean=-1, ear=2, arm={"el": (-3, -3), "paw": (-7, -6)}),
    F(off=(2, 0), lean=2, ear=2, arm={"el": (3, -2), "paw": (8, -2)}, mouth="open", cowl=1),
    F(off=(3, 0), lean=3, ear=2, arm={"el": (3, 1), "paw": (7, 4)}, cowl=1),
    F(off=(1, 0), crouch=1, lean=1, ear=2, arm={"el": (1, 0), "paw": (2, 0)}),
    F(crouch=2, lean=1, head=(0, 1), ear=2, arm=GUARD),
])
anim("signature", [  # shadow-dash leap and double claw (the smoke trail is an effect)
    F(crouch=4, lean=2, ear=3, eyes="wide", arm={"el": (-2, 2), "paw": (-5, 3)}, tail=-2),
    F(off=(-1, 0), crouch=5, lean=3, ear=3, eyes="wide", arm={"el": (-3, 2), "paw": (-7, 3)}, tail=-3),
    F(off=(3, -5), lean=3, ear=3, eyes="wide", mouth="open", arm={"el": (3, -2), "paw": (8, -3)},
      farm={"el": (3, -2), "paw": (8, -2)}, leg={"heel": (-3, -1), "toe": (-3, -1)},
      fleg={"heel": (-3, -1), "toe": (-3, -1)}, cowl=2),
    F(off=(5, -3), lean=3, ear=3, eyes="wide", arm={"el": (3, 2), "paw": (7, 5)}, farm={"el": (3, 2), "paw": (7, 6)},
      cowl=2),
    F(off=(5, 0), crouch=3, lean=3, ear=2, arm={"el": (2, 3), "paw": (5, 7)}),
    F(off=(2, 0), crouch=2, lean=1, ear=2, arm=GUARD),
])
anim("flinch", [
    F(off=(-2, 0), lean=-3, head=(-1, 0), eyes="closed", ear=3, arm={"el": (-1, -1), "paw": (-2, -3)}, tail=1),
    F(off=(-1, 0), lean=-1, eyes="half", ear=2, arm=GUARD),
])
anim("dodge", [
    F(off=(-1, 0), crouch=3, ear=2, arm=GUARD),
    F(off=(-5, -4), lean=-2, ear=3, arm={"el": (0, -2), "paw": (1, -5)},
      leg={"heel": (1, -1), "toe": (1, -1)}, fleg={"heel": (1, -1), "toe": (1, -1)}, cowl=2, tail=-2),
    F(off=(-6, 0), crouch=2, ear=1, arm=GUARD),
])
anim("knockout", [
    F(off=(-2, 0), lean=-3, head=(-1, 0), eyes="ko", ear=3, arm={"el": (-2, 2), "paw": (-5, 4)}),
    F(off=(-2, 0), crouch=4, lean=1, eyes="ko", ear=3, arm={"el": (0, 3), "paw": (-2, 6)}),
    F(off=(-2, 0), crouch=7, lean=4, head=(0, 4), eyes="ko", ear=3, arm={"el": (0, 4), "paw": (-2, 8)}),
    F(**{**KO, "off": (-2, 0)}),
])

# ---- Game poses (adult: athletic run, full hammer swings, bar-fight punches) ----
RUN = [({"knee": (2, -2), "heel": (3, -3), "toe": (5, -2)}, {"heel": (-4, 0), "toe": (-4, 0)}),
       ({"knee": (1, -1), "heel": (1, -1), "toe": (3, 0)}, {"knee": (0, -1), "heel": (-3, -2), "toe": (-2, -2)}),
       ({"heel": (-1, 0), "toe": (0, 0)}, {"knee": (1, -2), "heel": (0, -3), "toe": (2, -2)}),
       ({"heel": (-4, 0), "toe": (-4, 0)}, {"knee": (2, -2), "heel": (3, -3), "toe": (5, -2)}),
       ({"knee": (0, -1), "heel": (-3, -2), "toe": (-2, -2)}, {"knee": (1, -1), "heel": (1, -1), "toe": (3, 0)}),
       ({"knee": (1, -2), "heel": (0, -3), "toe": (2, -2)}, {"heel": (-1, 0), "toe": (0, 0)})]
anim("run", [F(lean=3, head=(0, 1), ear=2, bob=-1 if i in (1, 4) else 0, leg=RUN[i][0], fleg=RUN[i][1],
               arm={"el": (2 - (i % 3) * 2, 0), "paw": (4 - (i % 3) * 4, 1)},
               farm={"el": ((i % 3) * 2 - 2, 0), "paw": ((i % 3) * 4 - 4, 1)},
               cowl=1 + (i % 2), tail=-(i % 2)) for i in range(6)])
anim("jump", [
    F(crouch=4, lean=2, ear=2, arm={"el": (-2, 1), "paw": (-4, 2)}),
    F(off=(0, -6), lean=1, ear=3, arm={"el": (2, -4), "paw": (5, -8)}, farm={"el": (2, -3), "paw": (5, -6)},
      leg={"knee": (2, -3), "heel": (0, -4), "toe": (3, -3)}, fleg={"heel": (-3, -1), "toe": (-3, -1)}, cowl=2, tail=-2),
    F(crouch=3, lean=2, ear=1, arm={"el": (1, 1), "paw": (2, 2)}),
])
anim("vine_swing", [
    F(off=(0, -2), lean=-2 + dx, arm={"el_at": (34 + dx, 13), "paw_at": (36 + dx, 3.5)},
      leg={"heel": (-dx - 1, -2), "toe": (-dx - 1, -3)}, fleg={"heel": (-dx, -1), "toe": (-dx, -2)},
      cowl=s, tail=s, ear=2) for dx, s in ((-1, 0), (0, 1), (1, 2), (0, 1))
])
anim("fall", [
    F(off=(0, -3), lean=-3, eyes="wide", mouth="open", ear=3, arm=BACK,
      farm={"el_at": (41, 15), "paw_at": (48, 9)}, leg={"heel": (2, -2), "toe": (3, -2)}, cowl=-2, tail=-3),
    F(lean=-2, eyes="wide", mouth="open", ear=3, arm={"el": (-2, -5), "paw": (-4, -9)},
      farm={"el": (3, -4), "paw": (6, -7)}, cowl=-3, tail=-2),
    F(crouch=7, lean=4, head=(0, 3), eyes="ko", ear=3, arm={"el": (0, 4), "paw": (-2, 7)}),
])
anim("swing_right", [
    F(lean=-1, arm=BACK, ear=1),
    F(lean=1, arm=UP_N, ear=2),
    F(off=(1, 0), lean=3, arm={"el": (3, -1), "paw": (9, 0)}, ear=2, eyes="half", cowl=1),
    F(lean=1, arm={"el": (1, 0), "paw": (3, 1)}),
])
anim("swing_left", [
    F(lean=1, arm={"el": (2, 0), "paw": (4, -1)}),
    F(lean=-1, arm={"el": (-2, -2), "paw": (-6, -3)}, ear=1, tail=-1),
    F(lean=-3, arm={"el": (-5, -1), "paw": (-13, -2)}, ear=2, eyes="half", tail=-2, cowl=-1),
    F(lean=-1, arm={"el": (-1, 0), "paw": (-3, 0)}),
])
anim("swing_up", [
    F(crouch=2, arm={"el": (1, 2), "paw": (3, 4)}),
    F(lean=-1, arm={"el": (1, -3), "paw": (4, -6)}, ear=1),
    F(lean=-3, bob=-1, arm={"el_at": (34, 13), "paw_at": (37, 3)}, ear=2, eyes="half", cowl=-1),
    F(lean=-1, arm=REACH),
])
anim("swing_down", [
    F(lean=-2, arm=BACK, ear=1),
    F(lean=-1, arm=UP_N, ear=1),
    F(crouch=3, lean=4, head=(0, 2), arm={"el": (3, 3), "paw": (6, 10)}, ear=2, eyes="half"),
    F(crouch=1, lean=2, arm={"el": (1, 1), "paw": (3, 3)}),
])
FISTS = ({"el": (2, -2), "paw": (2, -5)}, {"el": (2, -3), "paw": (3, -6)})
anim("brawl_stance", [F(crouch=2, lean=1, head=(0, 1), ear=2, arm=FISTS[0], farm=FISTS[1],
                        bob=[0, -1, 0][i], tail=-1 - (i % 2)) for i in range(3)])
anim("parry", [
    F(ear=2, arm={"el": (2, -5), "paw": (4, -9)}, farm=FISTS[1]),
    F(off=(1, 0), lean=1, ear=3, eyes="half", arm={"el": (3, -6), "paw": (6, -11)}, farm={"el": (3, -5), "paw": (5, -9)}),
    F(crouch=1, lean=1, ear=2, arm=FISTS[0], farm=FISTS[1]),
])
anim("counter_a", [  # straight jab
    F(crouch=2, ear=2, arm={"el": (0, -1), "paw": (-2, -3)}, farm=FISTS[1]),
    F(off=(2, 0), lean=3, ear=3, arm={"el": (4, -3), "paw": (10, -4)}, farm=FISTS[1], mouth="open"),
    F(off=(1, 0), lean=1, ear=2, arm=FISTS[0], farm=FISTS[1]),
])
anim("counter_b", [  # rising uppercut
    F(crouch=4, lean=2, ear=2, arm={"el": (0, 2), "paw": (2, 4)}, farm=FISTS[1]),
    F(off=(2, -2), lean=-1, ear=3, arm=REACH, farm=FISTS[1], mouth="open", cowl=-1),
    F(off=(1, 0), lean=1, ear=2, arm=FISTS[0], farm=FISTS[1]),
])
anim("take_hit", [
    F(off=(-2, 0), lean=-3, head=(-1, 0), eyes="closed", ear=3, arm={"el": (-1, -1), "paw": (-2, -2)}, tail=1),
    F(off=(-1, 0), crouch=1, lean=-1, eyes="half", ear=2, arm=FISTS[0], farm=FISTS[1]),
])
anim("victory_taunt", [
    F(lean=-2, eyes="happy", mouth="open", arm=REACH, tail=-2),
    F(lean=-2, bob=-1, eyes="happy", mouth="open", arm=UP_N, tail=-3, cowl=-1),
    F(lean=-2, eyes="happy", arm=REACH, tail=-2),
])
anim("guard_stance", [F(crouch=3, lean=1, head=(0, 1), ear=2, arm={"el": (2, -3), "paw": (4, -6)},
                        farm=FISTS[1], bob=[0, -1, -1][i], tail=-1, cowl=-(i % 2)) for i in range(3)])
anim("stirring", [
    F(lean=2, head=(0, 1), arm={"el": (2, 2), "paw": (4, 5)}),
    F(lean=2, head=(0, 1), arm={"el": (3, 2), "paw": (7, 4)}, ear=1),
    F(lean=2, head=(0, 1), arm={"el": (2, 3), "paw": (5, 7)}, tail=-1),
])
anim("concentrating", [
    F(lean=-1, eyes="wide", arm={"el": (1, -2), "paw": (2, -5)}, farm={"el": (1, -2), "paw": (2, -4)}),
    F(lean=-1, bob=-1, eyes="wide", ear=-1, arm={"el": (1, -2), "paw": (2, -5)}, farm={"el": (1, -2), "paw": (2, -4)}),
])

if "--look" in sys.argv:  # a look test for a new form: keep only idle and blink
    A = {k: A[k] for k in ("idle", "blink")}

data = {
    "width": W, "height": H, "fps": 10, "palette": PAL,
    "dye_zones": {"main_fur": ["1", "2", "3", "4"], "accent_fur": ["5", "6", "7", "8"],
                  "eye_glow": ["e", "E", "f", "F"], "smoke": ["s", "S", "t", "T"]},
    # head / hand / torso: gear and hats snap here. aim: forearm angle in degrees
    # (0 = right, 90 = down) for picking a weapon rotation. root_dx: px the game moves him.
    "attach": {k: [a for _, a in v] for k, v in A.items()},
    "animations": {k: [r for r, _ in v] for k, v in A.items()},
}
json.dump(data, open(f"art/source/skerbie/adult_{FORM}.json", "w"), indent=1)
print("animations:", ", ".join(f"{k}[{len(v)}]" for k, v in A.items()))
