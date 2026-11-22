# Builds the Speed kid Skerbie (48x48) animations as pixel grids -> JSON.
# Look approved by George (2026-11-21): the approved baby's angular style
# (straight-edged polygons, flat faceted shading, narrowed glare, one fang),
# crouched and half-upright on bent hind legs, forepaws held up. Speed kid:
# sleek and lean, swept-back ears, a long thin tail, a tattered scarf.
#
# Every frame comes from frame(...), a small rig: each limb vertex belongs to a
# joint (hip/knee/heel/toe, shoulder/elbow/paw) and moves with it, so all the
# animations share one body. With no pose set, idle and blink come out exactly
# as approved. Effects and gear (the small hammer, weapons) are separate
# sprites that snap to the attach points recorded per frame.
# Run: python tools/build_kid_speed.py, then
#      python tools/render.py art/source/skerbie/kid_speed.json --out art/out/skerbie/kid_speed
import json, math

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

# Limbs: (x, y, joint). Hips/shoulders ride the body; the rest move with the pose.
LEG = [  # near hind leg; the far leg is the same shape shifted (see FAR_LEG_D)
    [(11, 28, "hip"), (22, 27, "hip"), (26, 37, "knee"), (20, 40, "knee"), (13, 35, "knee")],    # thigh
    [(20, 34.5, "knee"), (26, 37, "knee"), (18.5, 43.5, "heel"), (15, 42, "heel")],              # shin
    [(14, 41.5, "heel"), (18, 41, "heel"), (27, 45.5, "toe"), (26.5, 46.5, "toe"), (16.5, 46.5, "heel")],  # foot
]
FAR_LEG = [
    [(17, 28, "hip"), (27, 27, "hip"), (30, 36, "knee"), (24, 39.5, "knee"), (18, 35, "knee")],
    [(25, 34.5, "knee"), (30, 37, "knee"), (23, 43.5, "heel"), (19.5, 42, "heel")],
    [(18.5, 41.5, "heel"), (22.5, 41, "heel"), (31, 45.5, "toe"), (30.5, 46.5, "toe"), (21, 46.5, "heel")],
]
# Arms are built from real joints: shoulder -> elbow -> paw, each segment a solid
# tapered piece, so big swings (hammer overhead, uppercuts) keep their shape.
ARM_REST = {"sh": (27.5, 17.5), "el": (29, 24.5), "paw": (35.5, 28.5)}
FAR_ARM_REST = {"sh": (30.5, 17.5), "el": (32, 23.5), "paw": (37.5, 27.5)}


def seg(a, b, wa, wb, ext=0.6):
    # A tapered quad from a to b (widths wa, wb), nudged past both ends so joints overlap.
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dy) or 1
    ux, uy = dx / ln, dy / ln
    nx, ny = -uy, ux
    a2, b2 = (a[0] - ux * ext, a[1] - uy * ext), (b[0] + ux * ext, b[1] + uy * ext)
    return [(a2[0] + nx * wa / 2, a2[1] + ny * wa / 2), (b2[0] + nx * wb / 2, b2[1] + ny * wb / 2),
            (b2[0] - nx * wb / 2, b2[1] - ny * wb / 2), (a2[0] - nx * wa / 2, a2[1] - ny * wa / 2)]

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
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    hw, hh = max(1, (max(xs) - min(xs)) / 2), max(1, (max(ys) - min(ys)) / 2)
    return {(x, y): ((x + .5 - cx) / hw, (y + .5 - cy) / hh)
            for y in range(-6, H + 2) for x in range(-2, W + 2) if inside(poly, x, y)}


def tone(n, dark=0):
    lit = n[0] * LX + n[1] * LY
    t = 0 if lit > 0.5 else 1 if lit > -0.15 else 2 if lit > -0.55 else 3
    return min(3, t + dark)


def mv(poly, dx=0, dy=0):
    return [(x + dx, y + dy) for x, y in poly]


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def frame(bob=0, crouch=0, lean=0, head=(0, 0), ear=0, tail=0, scarf=0, eyes="open",
          mouth="closed", arm=None, farm=None, leg=None, fleg=None, off=(0, 0)):
    """One pose. All moves are in pixels.
    bob: body up(-)/down(+), feet planted.  crouch: sink the hips (+), knees push forward.
    lean: tip the upper body forward (+) or back toward upright (-).
    head: extra (dx, dy) for the head.      ear: sweep ears back (+).
    tail / scarf: flick the tips.          eyes / mouth: expression.
    arm / farm: {"el": (dx, dy), "paw": (dx, dy)} for the near / far arm.
    leg / fleg: {"knee": .., "heel": .., "toe": ..} for the near / far hind leg.
    off: (root_dx, dy). root_dx is not baked in; the game slides the sprite by it."""
    g, layer, order = {}, {}, {}
    z = [0]

    def paint(poly, part, ramp=FUR, dark=0, acc=None):
        z[0] += 1
        for p, n in poly_pts(poly).items():
            t = tone(n, dark)
            g[p] = (ACC if acc and acc(p) else ramp)[t]
            layer[p], order[p] = part, z[0]

    by = bob + crouch                  # whole body drop
    up = (lean, by)                    # shoulders, chest, neck
    hx, hy = min(head[0], 1) + lean, head[1] + by
    lift = hy + off[1]                 # head height counting jumps
    flat = max(0, ear - 1) * 0.6       # ears past a twitch flatten downward
    if lift + flat < -1:               # head raised: pin ears back so the tips stay in frame
        ear, flat = ear + (-1 - lift - flat) * 0.8, -1 - lift
    e, fy = ear, flat

    def limb(parts, pose, part, dark=0):
        # Hind legs: each vertex moves with its joint.
        pose = pose or {}
        joint = {"hip": (0, by),
                 "knee": add((crouch * 0.5, crouch * 0.5), pose.get("knee", (0, 0))),
                 "heel": pose.get("heel", (0, 0)), "toe": pose.get("toe", (0, 0))}
        for s_ in parts:
            paint([add((x, y), joint[j]) for x, y, j in s_], part, dark=dark)

    def arm_joints(rest, pose):
        pose = pose or {}
        # "el"/"paw" nudge a joint from rest; "el_at"/"paw_at" place it at an exact
        # pixel (used for overhead swings, where the paw must clear his head).
        sh = add(rest["sh"], up)
        el = pose["el_at"] if "el_at" in pose else add(add(rest["el"], up), pose.get("el", (0, 0)))
        pw = pose["paw_at"] if "paw_at" in pose else add(add(rest["paw"], up), pose.get("paw", (0, 0)))
        return sh, el, pw

    def arm_paint(rest, pose, part, dark=0):
        sh, el, pw = arm_joints(rest, pose)
        dx, dy = pw[0] - el[0], pw[1] - el[1]
        ln = math.hypot(dx, dy) or 1
        tip = (pw[0] + dx / ln * 2.5, pw[1] + dy / ln * 2.5)
        paint(seg(sh, el, 5, 3.8), part, dark=dark)     # upper arm
        paint(seg(el, pw, 3.8, 3.2), part, dark=dark)   # forearm
        paint(seg(pw, tip, 4.6, 3.6, 0.4), part, dark=dark)  # paw

    def upper(poly):
        return mv(poly, *up)

    # Far side, one shade darker.
    paint(mv([(28, 9), (35, 6.5), (21.5 + e, 0.5 + e * 0.5 + fy)], hx, hy), "far", dark=1)
    arm_paint(FAR_ARM_REST, farm, "far", dark=1)
    limb(FAR_LEG, fleg, "far", dark=1)
    # Long thin tail in one piece: back from the rump, then curling up.
    t = tail
    paint(mv([(14, 29), (16, 33.5), (9, 36), (4, 33), (1.5 + t, 26), (1 + t, 19), (3.5 + t, 20),
              (4.5 + t * 0.5, 27), (7, 31.5), (11, 31.5)], 0, by), "tail", acc=lambda p: p[1] <= 23 + by)
    # Tattered scarf streaming back from the neck.
    s = scarf
    paint(upper([(22, 14), (25, 18), (18, 20), (12, 22 + s), (13, 19.5 + s), (7, 20 + s),
                 (10, 17.5 + s * 0.5), (5, 16 + s * 0.5), (13, 14.5)]), "scarf", SCARF)
    # Torso: the hips stay with the legs, the chest and shoulders take the lean.
    torso = [(13, 30, 0), (16, 22, 1), (21, 16, 1), (29, 14, 1), (33, 18, 1), (32, 25, 1), (27, 31, 0),
             (23, 36, 0), (14, 36, 0)]
    tp = [(x + lean * k, y + by) for x, y, k in torso]
    chest = upper([(30, 16), (33, 18), (32, 25), (28, 30), (27.5, 21)])
    paint(tp, "body", acc=lambda p: inside(chest, *p))
    # Two hackle spikes on the upper back.
    paint(upper([(18, 20), (18, 13.5), (23, 17)]), "body", acc=lambda p: True)
    paint(mv([(14, 25), (12, 19), (18, 22)], lean * 0.5, by), "body", acc=lambda p: True)
    # Near hind leg: big thigh, shin back to a raised heel, long foot forward.
    limb(LEG, leg, "leg")
    # Scarf wrap around the neck.
    paint(upper([(22, 13.5), (30, 11.5), (32, 16), (24, 18.5)]), "wrap", SCARF)
    # Head: the baby's wedge, longer and sleeker.
    paint(mv([(26, 10), (28.5, 5), (34, 3), (39, 5), (46.5, 10), (45, 13), (38, 15.5), (30, 15.5), (27, 13.5)], hx, hy),
          "head", acc=lambda p: p[1] >= 14 + hy and 31 + hx <= p[0] <= 41 + hx)
    # Near ear: long, wide at the base, swept far back.
    paint(mv([(28, 8.5), (36, 5), (24 + e, 0 + e * 0.5 + fy)], hx, hy), "ear",
          acc=lambda p: inside(mv([(29.8, 7.4), (33.5, 6), (26 + e, 2.5 + e * 0.4 + fy)], hx, hy), *p))
    # Near arm, outlined so it reads over his dark body and head.
    arm_paint(ARM_REST, arm, "arm")

    # Seams: where a part sits on top of a different part, darken its edge pixel.
    for (x, y), part in list(layer.items()):
        if part == "far":
            continue
        for dx, dy in N4:
            q = (x + dx, y + dy)
            if q in layer and layer[q] != part and order[q] < order[(x, y)] and (layer[q] != "far" or part == "arm"):
                g[(x, y)] = "o" if part == "arm" else SCARF[3] if part in ("scarf", "wrap") else FUR[3]
                break
    for p in [p for p in g if not any((p[0] + dx, p[1] + dy) in g for dx, dy in N4)]:
        del g[p]
    filled = set(g)
    for (x, y) in filled:
        if any((x + dx, y + dy) not in filled for dx, dy in N4):
            g[(x, y)] = "o"

    # Eyes (true side view: the near eye only) and mouth.
    for j, row in enumerate(EYES[eyes]):
        for i, ch in enumerate(row):
            if ch != ".":
                g[(33 + hx + i, 7 + hy + j)] = ch
    if mouth == "open":
        for x in range(38, 47):
            g[(x + hx, 13 + hy)] = "o"
        for x in range(38, 45):
            g[(x + hx, 14 + hy)] = "o"
        g[(40 + hx, 14 + hy)] = "w"
    else:
        for x in range(39, 46):
            g[(x + hx, 13 + hy)] = "o"
        g[(40 + hx, 14 + hy)] = "w"

    ox, oy = off
    rows = ["".join(g.get((x, y - oy), ".") for x in range(W)) for y in range(H)]
    _, el, pw = arm_joints(ARM_REST, arm)
    d = math.hypot(pw[0] - el[0], pw[1] - el[1]) or 1
    grip = (pw[0] + (pw[0] - el[0]) / d * 1.5, pw[1] + (pw[1] - el[1]) / d * 1.5)  # centre of the paw
    aim = round(math.degrees(math.atan2(pw[1] - el[1], pw[0] - el[0])))
    attach = {"head": [34 + hx, 2 + hy + oy], "hand": [round(grip[0]), round(grip[1]) + oy], "aim": aim,
              "torso": [round(24 + lean * 0.5), 24 + by + oy], "root_dx": ox}
    return rows, attach


A = {}


def anim(name, frames):
    A[name] = frames


# Exact arm placements for poses where the paw must clear his head.
UP_N = {"el_at": (26, 9), "paw_at": (29, 1)}        # near paw straight up over his ears
UP_F = {"el_at": (30, 9), "paw_at": (33.5, 1.5)}    # far paw up
BACK = {"el_at": (23, 11), "paw_at": (19, 5)}       # wound back behind his head
REACH = {"el_at": (31, 10), "paw_at": (35, 2)}      # reaching up and forward

# ---- Home ----
anim("idle", [frame(), frame(bob=-1), frame(bob=-1, ear=1, scarf=-1, tail=-1), frame(ear=1, scarf=-1, tail=-1)])
anim("blink", [frame(eyes="half"), frame(eyes="closed")])

# Walk [6]: legs alternate, arms swing against them, scarf and tail trail.
STEP = [({"heel": (-3, 0), "toe": (-3, 0)}), ({"knee": (1, -2), "heel": (-1, -3), "toe": (1, -2)}),
        ({"knee": (2, -1), "heel": (2, -1), "toe": (3, 0)}), ({"heel": (3, 0), "toe": (3, 0)}),
        ({"heel": (1, 0), "toe": (1, 0)}), ({"heel": (-1, 0), "toe": (-1, 0)})]
anim("walk", [frame(bob=-1 if i in (1, 4) else 0, leg=STEP[i], fleg=STEP[(i + 3) % 6],
                    arm={"el": (-1 + (i % 3), 0), "paw": (-2 + (i % 3) * 2, 0)},
                    farm={"el": (1 - (i % 3), 0), "paw": (2 - (i % 3) * 2, 0)},
                    scarf=-1 if i % 2 else 0, tail=-1 if i in (2, 5) else 0) for i in range(6)])
anim("happy", [
    frame(crouch=2, eyes="happy"),
    frame(off=(0, -3), eyes="happy", arm=REACH, scarf=-1, tail=-1),
    frame(off=(0, -4), eyes="happy", arm=UP_N, farm=UP_F,
          scarf=-2, tail=-2, leg={"heel": (0, -1), "toe": (0, -1)}, fleg={"heel": (0, -1), "toe": (0, -1)}),
    frame(off=(0, -1), eyes="happy", arm={"el": (0, -1), "paw": (0, -2)}),
])
anim("eat", [  # holds food up to his mouth in both paws
    frame(arm={"el": (1, -2), "paw": (2, -7)}, farm={"el": (1, -2), "paw": (2, -6)}, head=(0, 1)),
    frame(arm={"el": (1, -2), "paw": (2, -8)}, farm={"el": (1, -2), "paw": (2, -7)}, head=(0, 1), mouth="open"),
    frame(arm={"el": (1, -2), "paw": (2, -7)}, farm={"el": (1, -2), "paw": (2, -6)}, head=(0, 2)),
    frame(arm={"el": (1, -2), "paw": (2, -8)}, farm={"el": (1, -2), "paw": (2, -7)}, head=(0, 1), mouth="open",
          tail=-1),
])
# Sleep: dozing where he sits, chin on his chest, arms folded. (Drifting smoke is an effect.)
CURL = dict(crouch=4, lean=-1, head=(-1, 5), ear=3, tail=1, arm={"el": (-1, 2), "paw": (-6, -2)},
            farm={"el": (-1, 2), "paw": (-6, -2)})
anim("sleep", [frame(**CURL, eyes="closed"), frame(**CURL, eyes="closed", bob=1)])
anim("tired", [
    frame(crouch=3, lean=2, head=(0, 2), ear=2, eyes="half", arm={"el": (0, 3), "paw": (-3, 6)}, tail=1),
    frame(crouch=4, lean=2, head=(0, 3), ear=2, eyes="half", arm={"el": (0, 3), "paw": (-3, 7)}, tail=1),
])
anim("petted", [
    frame(head=(-1, -1), lean=-1, eyes="happy", ear=2, tail=-1),
    frame(head=(-1, -2), lean=-1, eyes="happy", ear=3, tail=-2, bob=-1),
    frame(head=(-1, -1), lean=-1, eyes="happy", ear=2, tail=0),
])
KO = dict(crouch=9, lean=5, head=(0, 6), ear=3, eyes="ko", arm={"el": (0, 5), "paw": (-2, 9)},
          farm={"el": (0, 5), "paw": (-2, 9)}, tail=2)
anim("knocked_out", [
    frame(lean=-2, head=(-1, 0), eyes="ko", ear=3, arm={"el": (-2, 2), "paw": (-5, 4)}),
    frame(crouch=5, lean=2, head=(0, 3), eyes="ko", ear=3, arm={"el": (0, 3), "paw": (-2, 6)}),
    frame(**KO),
])
anim("knocked_out_loop", [frame(**KO), frame(**{**KO, "ear": 2, "tail": 1})])
# Working [4]: hammers with the small hammer (a separate sprite on the hand point).
anim("working", [
    frame(arm=BACK, ear=1),
    frame(arm=UP_N, lean=-1, ear=1),
    frame(crouch=1, lean=2, arm={"el": (1, -1), "paw": (4, 1)}, eyes="half"),
    frame(arm={"el": (0, -2), "paw": (0, -4)}),
])
# Carrying loot [4]: hugs the loot in both arms (loot snaps to the hand point) and trots.
HUG = ({"el": (1, 0), "paw": (0, -3)}, {"el": (1, 0), "paw": (0, -3)})
anim("carry", [frame(bob=-1 if i % 2 else 0, arm=HUG[0], farm=HUG[1], head=(0, -1),
                     leg=STEP[i * 3 // 2 % 6], fleg=STEP[(i * 3 // 2 + 3) % 6], tail=-1 if i % 2 else 0)
               for i in range(4)])
anim("cheer", [
    frame(crouch=2, eyes="wide", arm={"el": (0, 2), "paw": (-1, 2)}),
    frame(lean=-2, eyes="wide", mouth="open", arm=REACH, farm={"el_at": (33, 10), "paw_at": (37, 3)},
          tail=-2, scarf=-1),
    frame(lean=-2, bob=-1, eyes="happy", mouth="open", arm=UP_N, farm=UP_F, tail=-3, scarf=-2),
    frame(lean=-1, eyes="wide", arm={"el": (0, -3), "paw": (0, -6)}, tail=-1),
])
anim("catch", [
    frame(crouch=2, head=(0, 1)),
    frame(off=(0, -4), lean=-2, head=(0, -1), mouth="open", arm=REACH, farm={"el_at": (33, 10), "paw_at": (37, 3)},
          leg={"heel": (0, -1), "toe": (0, -1)}, scarf=-2, tail=-2),
    frame(crouch=1, arm={"el": (1, -2), "paw": (1, -4)}),
])

# ---- Fights (raids and Delve): claws and small fists ----
GUARD = {"el": (1, -1), "paw": (1, -3)}
anim("battle_stance", [frame(crouch=2, lean=1, head=(0, 1), ear=2, arm=GUARD, tail=-1 + (i % 2) * -1,
                             bob=-1 if i in (1, 2) else 0, scarf=-1 if i in (2, 3) else 0) for i in range(4)])
anim("basic_attack", [  # wind up, claw swipe forward, follow through
    frame(off=(-1, 0), crouch=2, lean=-1, ear=2, arm={"el": (-3, -3), "paw": (-7, -6)}),
    frame(off=(2, 0), lean=2, ear=2, arm={"el": (3, -2), "paw": (8, -2)}, mouth="open", scarf=1),
    frame(off=(3, 0), lean=3, ear=2, arm={"el": (3, 1), "paw": (7, 4)}, scarf=1),
    frame(off=(1, 0), crouch=1, lean=1, ear=2, arm={"el": (1, 0), "paw": (2, 0)}),
    frame(crouch=2, lean=1, head=(0, 1), ear=2, arm=GUARD),
])
anim("signature", [  # Shadow-dash leap and double claw (smoke trail is an effect)
    frame(crouch=4, lean=2, ear=3, eyes="wide", arm={"el": (-2, 2), "paw": (-5, 3)}, tail=-2),
    frame(off=(-1, 0), crouch=5, lean=3, ear=3, eyes="wide", arm={"el": (-3, 2), "paw": (-7, 3)}, tail=-3),
    frame(off=(3, -5), lean=3, ear=3, eyes="wide", mouth="open", arm={"el": (3, -2), "paw": (8, -3)},
          farm={"el": (3, -2), "paw": (8, -2)}, leg={"heel": (-3, -1), "toe": (-3, -1)},
          fleg={"heel": (-3, -1), "toe": (-3, -1)}, scarf=2),
    frame(off=(5, -3), lean=3, ear=3, eyes="wide", arm={"el": (3, 2), "paw": (7, 5)},
          farm={"el": (3, 2), "paw": (7, 6)}, scarf=2),
    frame(off=(5, 0), crouch=3, lean=3, ear=2, arm={"el": (2, 3), "paw": (5, 7)}),
    frame(off=(2, 0), crouch=2, lean=1, ear=2, arm=GUARD),
])
anim("flinch", [
    frame(off=(-2, 0), lean=-3, head=(-1, 0), eyes="closed", ear=3, arm={"el": (-1, -1), "paw": (-2, -3)}, tail=1),
    frame(off=(-1, 0), lean=-1, eyes="half", ear=2, arm=GUARD),
])
anim("dodge", [
    frame(off=(-1, 0), crouch=3, ear=2, arm=GUARD),
    frame(off=(-5, -4), lean=-2, ear=3, arm={"el": (0, -2), "paw": (1, -5)},
          leg={"heel": (1, -1), "toe": (1, -1)}, fleg={"heel": (1, -1), "toe": (1, -1)}, scarf=2, tail=-2),
    frame(off=(-6, 0), crouch=2, ear=1, arm=GUARD),
])
anim("knockout", [
    frame(off=(-2, 0), lean=-3, head=(-1, 0), eyes="ko", ear=3, arm={"el": (-2, 2), "paw": (-5, 4)}),
    frame(off=(-2, 0), crouch=4, lean=1, eyes="ko", ear=3, arm={"el": (0, 3), "paw": (-2, 6)}),
    frame(off=(-2, 0), crouch=7, lean=4, head=(0, 4), eyes="ko", ear=3, arm={"el": (0, 4), "paw": (-2, 8)}),
    frame(**{**KO, "off": (-2, 0)}),
])

# ---- Game poses (kid versions, ART_BRIEF §4.1) ----
# Jungle Run: scrambles and leaps; swings from the vine by one paw.
RUN = [({"knee": (2, -2), "heel": (3, -3), "toe": (5, -2)}, {"heel": (-4, 0), "toe": (-4, 0)}),
       ({"knee": (1, -1), "heel": (1, -1), "toe": (3, 0)}, {"knee": (0, -1), "heel": (-3, -2), "toe": (-2, -2)}),
       ({"heel": (-1, 0), "toe": (0, 0)}, {"knee": (1, -2), "heel": (0, -3), "toe": (2, -2)}),
       ({"heel": (-4, 0), "toe": (-4, 0)}, {"knee": (2, -2), "heel": (3, -3), "toe": (5, -2)}),
       ({"knee": (0, -1), "heel": (-3, -2), "toe": (-2, -2)}, {"knee": (1, -1), "heel": (1, -1), "toe": (3, 0)}),
       ({"knee": (1, -2), "heel": (0, -3), "toe": (2, -2)}, {"heel": (-1, 0), "toe": (0, 0)})]
anim("run", [frame(lean=3, head=(0, 1), ear=2, bob=-1 if i in (1, 4) else 0, leg=RUN[i][0], fleg=RUN[i][1],
                   arm={"el": (2 - (i % 3) * 2, 0), "paw": (4 - (i % 3) * 4, 1)},
                   farm={"el": ((i % 3) * 2 - 2, 0), "paw": ((i % 3) * 4 - 4, 1)},
                   scarf=1 + (i % 2), tail=-(i % 2)) for i in range(6)])
anim("jump", [
    frame(crouch=4, lean=2, ear=2, arm={"el": (-2, 1), "paw": (-4, 2)}),
    frame(off=(0, -6), lean=1, ear=3, arm={"el": (2, -4), "paw": (5, -8)}, farm={"el": (2, -3), "paw": (5, -6)},
          leg={"knee": (2, -3), "heel": (0, -4), "toe": (3, -3)}, fleg={"heel": (-3, -1), "toe": (-3, -1)},
          scarf=2, tail=-2),
    frame(crouch=3, lean=2, ear=1, arm={"el": (1, 1), "paw": (2, 2)}),
])
anim("vine_swing", [  # the vine grips at the hand point, overhead
    frame(off=(0, -2), lean=-2 + dx, arm={"el_at": (28 + dx, 9), "paw_at": (30 + dx, 1)},
          leg={"heel": (-dx - 1, -2), "toe": (-dx - 1, -3)}, fleg={"heel": (-dx, -1), "toe": (-dx, -2)},
          scarf=s, tail=s, ear=2) for dx, s in ((-1, 0), (0, 1), (1, 2), (0, 1))
])
anim("fall", [
    frame(off=(0, -3), lean=-3, eyes="wide", mouth="open", ear=3, arm=BACK,
          farm={"el_at": (33, 10), "paw_at": (38, 4)}, leg={"heel": (2, -2), "toe": (3, -2)}, scarf=-2, tail=-3),
    frame(off=(0, 1), lean=-2, eyes="wide", mouth="open", ear=3, arm={"el": (-2, -5), "paw": (-4, -9)},
          farm={"el": (3, -4), "paw": (6, -7)}, scarf=-3, tail=-2),
    frame(off=(0, 2), crouch=7, lean=4, head=(0, 3), eyes="ko", ear=3, arm={"el": (0, 4), "paw": (-2, 7)}),
])
# Block Party: swings the small hammer (hand point + aim angle) toward each direction.
anim("swing_right", [
    frame(lean=-1, arm=BACK, ear=1),
    frame(lean=1, arm=UP_N, ear=2),
    frame(off=(1, 0), lean=3, arm={"el": (3, -1), "paw": (9, 0)}, ear=2, eyes="half", scarf=1),
    frame(lean=1, arm={"el": (1, 0), "paw": (3, 1)}),
])
anim("swing_left", [  # a backhand sweep behind him
    frame(lean=1, arm={"el": (2, 0), "paw": (4, -1)}),
    frame(lean=-1, arm={"el": (-2, -2), "paw": (-6, -3)}, ear=1, tail=-1),
    frame(lean=-3, arm={"el": (-5, -1), "paw": (-13, -2)}, ear=2, eyes="half", tail=-2, scarf=-1),
    frame(lean=-1, arm={"el": (-1, 0), "paw": (-3, 0)}),
])
anim("swing_up", [
    frame(crouch=2, arm={"el": (1, 2), "paw": (3, 4)}),
    frame(lean=-1, arm={"el": (1, -3), "paw": (4, -6)}, ear=1),
    frame(lean=-3, bob=-1, arm={"el_at": (27, 9), "paw_at": (31, 0.5)}, ear=2, eyes="half", scarf=-1),
    frame(lean=-1, arm=REACH),
])
anim("swing_down", [
    frame(lean=-2, arm=BACK, ear=1),
    frame(lean=-1, arm=UP_N, ear=1),
    frame(crouch=3, lean=4, head=(0, 2), arm={"el": (3, 3), "paw": (6, 10)}, ear=2, eyes="half"),
    frame(crouch=1, lean=2, arm={"el": (1, 1), "paw": (3, 3)}),
])
# Bar Brawl: small fists and forepaws.
FISTS = ({"el": (2, -2), "paw": (2, -5)}, {"el": (2, -3), "paw": (3, -6)})
anim("brawl_stance", [frame(crouch=2, lean=1, head=(0, 1), ear=2, arm=FISTS[0], farm=FISTS[1],
                            bob=[0, -1, 0][i], tail=-1 - (i % 2)) for i in range(3)])
anim("parry", [
    frame(lean=0, ear=2, arm={"el": (2, -5), "paw": (4, -9)}, farm=FISTS[1]),
    frame(off=(1, 0), lean=1, ear=3, eyes="half", arm={"el": (3, -6), "paw": (6, -11)}, farm={"el": (3, -5), "paw": (5, -9)}),
    frame(crouch=1, lean=1, ear=2, arm=FISTS[0], farm=FISTS[1]),
])
anim("counter_a", [  # straight jab
    frame(crouch=2, lean=0, ear=2, arm={"el": (0, -1), "paw": (-2, -3)}, farm=FISTS[1]),
    frame(off=(2, 0), lean=3, ear=3, arm={"el": (4, -3), "paw": (10, -4)}, farm=FISTS[1], mouth="open"),
    frame(off=(1, 0), lean=1, ear=2, arm=FISTS[0], farm=FISTS[1]),
])
anim("counter_b", [  # rising uppercut
    frame(crouch=4, lean=2, ear=2, arm={"el": (0, 2), "paw": (2, 4)}, farm=FISTS[1]),
    frame(off=(2, -2), lean=-1, ear=3, arm=REACH, farm=FISTS[1], mouth="open", scarf=-1),
    frame(off=(1, 0), lean=1, ear=2, arm=FISTS[0], farm=FISTS[1]),
])
anim("take_hit", [
    frame(off=(-2, 0), lean=-3, head=(-1, 0), eyes="closed", ear=3, arm={"el": (-1, -1), "paw": (-2, -2)}, tail=1),
    frame(off=(-1, 0), crouch=1, lean=-1, eyes="half", ear=2, arm=FISTS[0], farm=FISTS[1]),
])
anim("victory_taunt", [
    frame(lean=-2, eyes="happy", mouth="open", arm=REACH, tail=-2),
    frame(lean=-2, bob=-1, eyes="happy", mouth="open", arm=UP_N, tail=-3, scarf=-1),
    frame(lean=-2, eyes="happy", arm=REACH, tail=-2),
])
# Word Rush: braced guard on the cliff path.
anim("guard_stance", [frame(crouch=3, lean=1, head=(0, 1), ear=2, arm={"el": (2, -3), "paw": (4, -6)},
                            farm=FISTS[1], bob=[0, -1, -1][i], tail=-1, scarf=-(i % 2)) for i in range(3)])
# Potion Brew: stirs the cauldron with a forepaw.
anim("stirring", [
    frame(lean=2, head=(0, 1), arm={"el": (2, 2), "paw": (4, 5)}),
    frame(lean=2, head=(0, 1), arm={"el": (3, 2), "paw": (7, 4)}, ear=1),
    frame(lean=2, head=(0, 1), arm={"el": (2, 3), "paw": (5, 7)}, tail=-1),
])
# Rune Lock: very still, eyes wide and burning, paws together.
anim("concentrating", [
    frame(lean=-1, eyes="wide", arm={"el": (1, -2), "paw": (2, -5)}, farm={"el": (1, -2), "paw": (2, -4)}),
    frame(lean=-1, bob=-1, eyes="wide", ear=-1, arm={"el": (1, -2), "paw": (2, -5)}, farm={"el": (1, -2), "paw": (2, -4)}),
])

data = {
    "width": W, "height": H, "fps": 10, "palette": PAL,
    "dye_zones": {"main_fur": ["1", "2", "3", "4"], "accent_fur": ["5", "6", "7", "8"],
                  "eye_glow": ["e", "E", "f", "F"], "smoke": ["s", "S", "t", "T"]},
    # head / hand / torso: gear and hats snap here. aim: the forearm angle in degrees
    # (0 = pointing right, 90 = down), for picking a weapon rotation. root_dx: px the game moves him.
    "attach": {k: [a for _, a in v] for k, v in A.items()},
    "animations": {k: [r for r, _ in v] for k, v in A.items()},
}
json.dump(data, open("art/source/skerbie/kid_speed.json", "w"), indent=1)
print("animations:", ", ".join(f"{k}[{len(v)}]" for k, v in A.items()))
