# Builds the baby Skerbie (32x32) animations as pixel grids -> JSON.
# Angular, aggressive look (approved by George, 2026-11-21): sharp shapes built
# from polygons, a low crouch with raised hackles, narrowed glaring eyes and a fang.
# Every frame is made by frame(...) with a few pose dials, so all animations
# share one body. Effects (smoke, sparkles) are separate sprites, never baked in.
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
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))

# Legs as (hip-left, hip-right, knee-right, foot-right, foot-left, knee-left).
LEGS = {
    "far_back":   [(10, 21), (14.5, 21), (14, 26), (14, 29.5), (11.5, 29.5), (11.5, 25)],
    "far_front":  [(20, 20), (24, 20), (24, 24.75), (24, 29.5), (21.5, 29.5), (21, 24)],
    "near_back":  [(5.5, 21), (11, 21), (10, 26), (9.5, 29.5), (6.5, 29.5), (7.5, 25)],
    "near_front": [(16.5, 20), (20.5, 20), (20.25, 24.75), (20, 29.5), (17.5, 29.5), (17.5, 24)],
}

# Eye stamps: '.' leaves the fur underneath. Near eye 5x4, far eye 2x3.
EYES = {
    "open":   (["oo...", "eEoo.", "EEEEo", ".fffF"], ["o.", "Eo", "fF"]),
    "half":   (["oo...", "ooooo", "EEEEo", ".fffF"], ["o.", "oo", "fF"]),
    "closed": (["oo...", "22...", "ooooo", ".222."], ["o.", "2.", "oo"]),
    "happy":  (["oo...", "oeEEo", "Ef.fE", "o...o"], ["o.", "Eo", "o."]),   # glowing smug squint
    "wide":   (["o....", "eEEo.", "EEEEo", "ffffF"], ["o.", "Eo", "fF"]),
    "ko":     (["fo.fo", ".ffo.", ".ffo.", "fo.fo"], ["o.", "fo", "f."]),   # dim X eyes
}


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
            for y in range(-8, H + 4) for x in range(-4, W + 4) if inside(poly, x, y)}


def tone(n, dark=0):
    # Straight-line thresholds give flat, faceted planes instead of round shading.
    lit = n[0] * LX + n[1] * LY
    t = 1 if lit > 0.5 else 2 if lit > -0.15 else 3 if lit > -0.55 else 4
    return min(4, t + dark)


def mv(poly, dx=0, dy=0):
    return [(x + dx, y + dy) for x, y in poly]


def leg(name, body_dy, foot):
    # Hips follow the body, feet move by `foot`, knees go halfway between.
    fdx, fdy = foot
    hl, hr, kr, fr, fl, kl = LEGS[name]
    # Knees stay put on a breath (as in the approved idle) and only sink when he crouches.
    kdx, kdy = fdx / 2, (max(0, body_dy) + fdy) / 2
    return [mv([hl], 0, body_dy)[0], mv([hr], 0, body_dy)[0], mv([kr], kdx, kdy)[0],
            mv([fr], fdx, fdy)[0], mv([fl], fdx, fdy)[0], mv([kl], kdx, kdy)[0]]


def frame(bob=0, ear=0, tail=0, eyes="open", head=(0, 0), crouch=0, feet=None,
          mouth="closed", off=(0, 0), fold=False, rear=0):
    """One pose.
    bob: chest/back up(-)/down(+), feet stay put.   crouch: whole body lower (+).
    head: extra (dx, dy) for head, ears and face.    ear: sweep ears back (+).
    tail: flick the tail tip up(-)/down(+).          feet: {leg: (dx, dy)} foot moves.
    mouth: closed / open.   off: move the whole sprite (jumps).
    fold: tuck all legs under the body (lying down).
    rear: rear up on the hind legs by this many pixels (chest, forelegs and head rise)."""
    feet = dict(feet or {})
    if rear:
        head = (head[0], head[1] - rear)
        for k in ("near_front", "far_front"):
            fx, fy = feet.get(k, (0, 0))
            feet[k] = (fx + 1, fy - rear - 1)  # forepaws come off the ground
    g, layer = {}, {}

    def paint(poly, part, dark=0, acc=None):
        for p, n in poly_pts(poly).items():
            t = tone(n, dark)
            g[p] = str(t + 4) if (acc and acc(p)) else str(t)
            layer[p] = part

    b, c = bob, crouch
    hx, hy = head[0], head[1] + b + c
    top = b + c  # back and shoulders
    # Far side, drawn first and one shade darker.
    flat = max(0, ear - 1) * 0.8  # ears past a twitch also flatten downward
    sweep = 0
    lift = hy + off[1]  # how high the head sits, counting jumps
    if lift + flat < -1:  # head raised: pin the ears back so the tips stay inside the frame
        sweep, flat = (-1 - lift - flat) * 0.8, -1 - lift
    ear += sweep
    paint(mv([(11.5, 12.5), (17.5, 11), (11.5 + ear * 0.5, 1.5 + flat)], hx, hy), "farear", dark=1)
    r = rear

    def hip(name):
        return top - (r if "front" in name else 0)

    for name in ("far_back", "far_front"):
        if not fold:
            paint(leg(name, hip(name), feet.get(name, (0, 0))), "farleg", dark=1)
    # Stub tail, a short spike flicking up and back.
    paint(mv([(4.5, 15), (7.5, 17), (6, 20), (2.5, 19), (0.5, 11.5 + tail - top)], 0, top), "tail",
          acc=lambda p: p[1] <= 14 + tail)
    # Hunched, wedge-shaped body: high shoulders, low haunch.
    paint([(4, 19 + top), (10, 15 + top - r * 0.4), (17, 14 + top - r * 0.8), (21, 18 + top - r),
           (20, 24 + c - r), (9, 24 + c), (4, 22 + c)],
          "body", acc=lambda p: p[1] >= 22 + c - r * (p[0] - 9) / 11 and 11 <= p[0] <= 18)
    # Raised hackles: a sawtooth ridge of accent fur along the back.
    for x0, tp, lift in ((7, 12, 0.15), (10.5, 10.5, 0.4), (14, 11, 0.7)):
        paint(mv([(x0, 17), (x0 + 1.5, tp), (x0 + 4, 16)], 0, top - r * lift), "hackle", acc=lambda p: True)
    # Near legs: angled haunch at the back, straight braced foreleg.
    for name in ("near_back", "near_front"):
        if fold:
            # Tucked paws: short wedges sticking out under the chest and haunch.
            x0 = 6 if name == "near_back" else 17
            paint([(x0, 23 + c), (x0 + 5, 23 + c), (x0 + 5.5, 25.5 + c), (x0 - 0.5, 25.5 + c)], "leg")
        else:
            paint(leg(name, hip(name), feet.get(name, (0, 0))), "leg")
    # Lowered, forward head with a long pointed snout.
    paint(mv([(14, 15), (16, 11), (21, 9), (25, 11), (30.5, 14.5), (29, 17), (23, 19.5), (17, 19.5)], hx, hy),
          "head", acc=lambda p: p[1] >= 18 + hy and 17 + hx <= p[0] <= 26 + hx)
    # Near ear: tall, sharp, swept back.
    paint(mv([(16, 11.5), (23, 10), (16.5 - ear, 0 + flat)], hx, hy), "ear",
          acc=lambda p: inside(mv([(17.8, 10.5), (21, 10), (17.4 - ear, 3 + flat)], hx, hy), *p))

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
    for p in [p for p in g if not any((p[0] + dx, p[1] + dy) in g for dx, dy in N4)]:
        del g[p]
    filled = set(g)
    for (x, y) in filled:
        if any((x + dx, y + dy) not in filled for dx, dy in N4):
            g[(x, y)] = "o"

    # Eyes: the brow slopes down toward the snout.
    ex, ey = 20 + hx, 12 + hy
    near, far = EYES[eyes]
    for j, row in enumerate(near):
        for i, ch in enumerate(row):
            if ch != ".":
                g[(ex + i, ey + j)] = ch
    for j, row in enumerate(far):
        for i, ch in enumerate(row):
            if ch != ".":
                g[(26 + hx + i, ey + 1 + j)] = ch
    # Mouth and a single fang.
    my = 16 + hy
    if mouth == "open":
        for x in range(24, 30):
            g[(x + hx, my)] = "o"
        for x in range(24, 29):
            g[(x + hx, my + 1)] = "o"
        g[(25 + hx, my + 1)] = "w"
    else:
        for x in range(24, 29):
            g[(x + hx, my)] = "o"
        g[(25 + hx, my + 1)] = "w"
    ox, oy = off
    rows = ["".join(g.get((x - ox, y - oy), ".") for x in range(W)) for y in range(H)]
    mouth_pt = [27 + hx + ox, 17 + hy + oy]
    return rows, mouth_pt


# ---- Animations (frame counts from ART_BRIEF §4.1) ----
A = {}


def anim(name, frames):
    A[name] = frames


# Idle: breathe (1 px bob), ears twitch and the tail flicks one frame behind.
anim("idle", [frame(), frame(bob=-1), frame(bob=-1, ear=1), frame(ear=1, tail=-1)])
anim("blink", [frame(eyes="half"), frame(eyes="closed")])

# Walk [6]: diagonal pairs swing together; the body bobs on the passing frames.
step = [(-1.5, 0), (0, -2), (1.5, 0)]  # back, swing (lifted), forward
pairs = []
for i in range(6):
    a = step[[0, 1, 2, 2, 1, 0][i]] if i < 3 else step[[2, 2, 1, 0, 0, 1][i]]
    pairs.append(i)
walk = []
phase = [(-1.5, 0), (-0.5, -2), (1, -1), (1.5, 0), (0.5, 0), (-0.5, 0)]
for i in range(6):
    a, bph = phase[i], phase[(i + 3) % 6]
    walk.append(frame(bob=-1 if i in (1, 4) else 0, tail=-1 if i in (2, 5) else 0, ear=1 if i in (2, 3) else 0,
                      feet={"near_back": a, "far_front": a, "far_back": bph, "near_front": bph}))
anim("walk", walk)

# Happy bounce [4]: squash, hop up, peak, land. Happy squint, tail up.
anim("happy", [
    frame(crouch=1, eyes="happy", tail=-1),
    frame(off=(0, -2), eyes="happy", tail=-2, ear=-1),
    frame(off=(0, -3), eyes="happy", tail=-1, feet={k: (0, -1) for k in LEGS}),
    frame(off=(0, -1), eyes="happy", tail=0),
])

# Eat [4]: head dips to the ground and chomps.
anim("eat", [
    frame(head=(1, 2)),
    frame(head=(2, 4), mouth="open", bob=1),
    frame(head=(2, 5), bob=1),
    frame(head=(2, 4), mouth="open", bob=1, tail=-1),
])

# Sleep [2]: lying down, legs tucked, head resting, slow breathing. (Smoke is an effect.)
anim("sleep", [
    frame(crouch=4, fold=True, head=(0, 3), eyes="closed", ear=2),
    frame(crouch=4, fold=True, head=(0, 3), eyes="closed", ear=2, bob=-1),
])

# Tired slump [2]: sagging body, drooping head, half-closed eyes.
anim("tired", [
    frame(crouch=2, head=(0, 2), eyes="half", ear=2, tail=1),
    frame(crouch=2, head=(0, 3), eyes="half", ear=2, tail=1, bob=1),
])

# Petted [3]: leans up into the hand, smug squint, ears flatten, tail wags.
anim("petted", [
    frame(head=(-1, -1), eyes="happy", ear=2, tail=-1),
    frame(head=(-1, -2), eyes="happy", ear=3, tail=-2, bob=-1),
    frame(head=(-1, -1), eyes="happy", ear=2, tail=0),
])

# Knocked out [3], then a 2-frame loop lying flat.
anim("knocked_out", [
    frame(head=(-1, 1), eyes="ko", ear=2, crouch=1),
    frame(head=(0, 3), eyes="ko", ear=3, crouch=3, fold=True),
    frame(head=(1, 5), eyes="ko", ear=3, crouch=5, fold=True, tail=2),
])
anim("knocked_out_loop", [
    frame(head=(1, 5), eyes="ko", ear=3, crouch=5, fold=True, tail=2),
    frame(head=(1, 5), eyes="ko", ear=2, crouch=5, fold=True, tail=1),
])

# Working [4]: the baby has no tools, so he digs and slams with a forepaw.
anim("working", [
    frame(head=(1, 1), feet={"near_front": (1, -3)}),
    frame(head=(1, 2), feet={"near_front": (2, -5)}, ear=1),
    frame(head=(1, 2), bob=1, feet={"near_front": (2, 0)}, tail=-1),
    frame(head=(1, 1), feet={"near_front": (1, -1)}),
])

# Carrying loot [4]: a proud head-up trot; the loot sprite snaps to the "mouth" point.
carry = []
cphase = [(-1, 0), (0, -2), (1, 0), (0, 0)]
for i in range(4):
    a, bph = cphase[i], cphase[(i + 2) % 4]
    carry.append(frame(head=(0, -2), bob=-1 if i % 2 else 0, tail=-1 if i in (1, 2) else 0,
                       feet={"near_back": a, "far_front": a, "far_back": bph, "near_front": bph}))
anim("carry", carry)

# Level-up cheer [4]: rears up on his hind legs, mouth open, eyes wide.
anim("cheer", [
    frame(crouch=1, eyes="wide"),
    frame(rear=3, eyes="wide", mouth="open", tail=-2),
    frame(rear=4, eyes="happy", mouth="open", tail=-2),
    frame(rear=1, eyes="wide", tail=-1),
])

# Catch [3] (foraging): crouch, snap upward with an open mouth, land.
anim("catch", [
    frame(crouch=2, head=(0, 1), tail=1),
    frame(off=(0, -3), head=(1, -3), mouth="open", ear=1, tail=-2, feet={k: (0, -1) for k in LEGS}),
    frame(crouch=1, head=(0, 0), tail=-1),
])

data = {
    "width": W, "height": H, "fps": 10, "palette": PAL,
    "dye_zones": {"main_fur": ["1", "2", "3", "4"], "accent_fur": ["5", "6", "7", "8"],
                  "eye_glow": ["e", "E", "f", "F"], "smoke": ["s", "S", "t", "T"]},
    "attach": {name: [{"mouth": m} for _, m in frames] for name, frames in A.items()},
    "animations": {name: [rows for rows, _ in frames] for name, frames in A.items()},
}
json.dump(data, open("art/source/skerbie/baby.json", "w"), indent=1)
print("animations:", ", ".join(f"{k}[{len(v)}]" for k, v in A.items()))
