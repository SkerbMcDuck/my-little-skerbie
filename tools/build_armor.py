# Builds the 6 armours (ART_BRIEF §5) as fitted overlays for every kid and adult form,
# with a row for every animation, so the armour moves with him in every pose.
# How it fits: the body builders save, per frame, which visible pixel is torso / arm / leg /
# head and where the near shoulder, elbow, paw, hip and knee are (art/source/skerbie/parts/,
# generated). Each armour piece claims the visible pixels of the right body part in the right
# stretch (e.g. "upper arm from the shoulder to halfway to the elbow"), gets its own flat
# faceted shading lit from the top-left, an outline where it ends (so it reads as sitting on
# top of the fur), and its pattern (rivets, ribs, chain links...). Only visible pixels are
# claimed, so the near arm still hides the chest plate where it crosses in front.
# The game draws the equipped armour's overlay on top of the body frame. Armour is gear:
# none of its colours are dye zones. (The Warden's own bolted-on iron is part of his body.)
# Usage: python tools/build_kid.py <form> and python tools/build_adult.py <form> first, then
#        python tools/build_armor.py, then render art/source/gear/armor/<armour>_<form>.json
import json, math, os, random

FORMS = ["kid_speed", "kid_strength", "kid_mind",
         "adult_stalker", "adult_juggernaut", "adult_occultist", "adult_warden"]
PAL = {
    "o": "#0f0d14",
    "L": "#557a5c", "M": "#3e5a46", "N": "#2c4234",        # moss leaves
    "a": "#7a5636", "b": "#3b2a22", "s": "#bfae8c",        # leather, dark leather, stitching
    "w": "#c9cfd6", "i": "#5a5e66", "h": "#33303d",        # iron
    "r": "#8b7a4a",                                        # rust / bone shadow
    "q": "#bfae8c", "u": "#a8945e",                        # bone
    "x": "#4a3a5c", "y": "#23212b", "z": "#17151c",        # shadow-iron: dusky sheen, black iron
}
RAMP = {"leaf": "LMNN", "leather": "aabb", "iron": "wiih", "bone": "qqur", "shadow": "xxyz"}
LX, LY = -0.6, -0.8
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def proj(p, a, b):
    # Where pixel p falls along segment a->b (t), and how far from it (d).
    ax, ay, bx, by = *a, *b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy or 1
    t = ((p[0] + .5 - ax) * dx + (p[1] + .5 - ay) * dy) / L2
    cx, cy = ax + dx * t, ay + dy * t
    return t, math.hypot(p[0] + .5 - cx, p[1] + .5 - cy)


def region(parts, J, s, kind, t0, t1, extra=0):
    pix = {(x, y): c for y, r in enumerate(parts) for x, c in enumerate(r) if c != "."}
    sh, el, pw, hip, kn = (tuple(J[k]) for k in ("sh", "el", "pw", "hip", "knee"))
    if kind == "torso":  # chest band: from t0 px above the shoulder line to t1 px below the hip line
        y0, y1 = sh[1] - t0 * s, hip[1] + t1 * s
        return {p for p, c in pix.items() if c == "b" and y0 <= p[1] <= y1}
    if kind == "neck":  # neck and the top of the shoulders, plus the back of the head
        return {p for p, c in pix.items() if (c == "b" and p[1] <= sh[1] + t1 * s)
                or (c == "h" and p[0] <= sh[0] + extra * s and p[1] <= sh[1] - 2 * s)}  # ears ('e') stay bare
    seg_a, seg_b, code = {"upper": (sh, el, "a"), "fore": (el, pw, "a"), "thigh": (hip, kn, "l")}[kind]
    out = set()
    for p, c in pix.items():
        if c == code:
            t, d = proj(p, seg_a, seg_b)
            if t0 <= t <= t1 and d <= 6 * s:
                out.add(p)
    return out


def shade(piece, ramp):
    xs, ys = [p[0] for p in piece], [p[1] for p in piece]
    cx, cy = (min(xs) + max(xs) + 1) / 2, (min(ys) + max(ys) + 1) / 2
    hw, hh = max(1, (max(xs) - min(xs) + 1) / 2), max(1, (max(ys) - min(ys) + 1) / 2)
    g = {}
    for p in piece:
        lit = (p[0] + .5 - cx) / hw * LX + (p[1] + .5 - cy) / hh * LY
        g[p] = ramp[0 if lit > 0.5 else 1 if lit > -0.15 else 2 if lit > -0.55 else 3]
    return g


# Each armour: list of pieces (kind, t0, t1, material, extra) and a pattern function.
ARMORS = {
    "leaf_wrap": [("torso", -3, -2, "leaf", 0)],                                         # common
    "leather_vest": [("torso", 1, 0, "leather", 0), ("upper", 0, 0.3, "leather", 0)],    # common
    "scrap_plate": [("torso", 1, -4, "iron", 0), ("upper", 0, 0.55, "iron", 0),
                    ("thigh", 0, 0.45, "iron", 0)],                                      # rare
    "chain_cowl": [("neck", 0, 4, "iron", 3), ("upper", 0, 0.35, "iron", 0)],             # rare
    "bone_armor": [("torso", 1, -2, "bone", 0), ("upper", 0, 0.5, "bone", 0),
                   ("fore", 0.45, 1.0, "bone", 0)],                                      # epic
    "shadow_iron_plate": [("torso", 1, 1, "shadow", 0), ("upper", 0, 0.6, "shadow", 0),
                          ("fore", 0.35, 1.0, "shadow", 0), ("thigh", 0, 0.6, "shadow", 0)],  # epic
}


def pattern(name, piece, g, k, rnd):
    if not piece:
        return
    ys = [p[1] for p in piece]
    top = min(ys)
    inner = [p for p in piece if g.get(p) != "o"]
    if name == "leaf_wrap":  # a ragged top edge, leaf veins
        for p in list(piece):
            if p[1] - top < (p[0] // 2) % 2 + 1:
                g.pop(p, None)
        for p in inner:
            if (p[0] + p[1]) % 5 == 0 and p in g:
                g[p] = "L"
    elif name == "leather_vest" and k == 0:  # a stitched seam down the front
        fx = max(p[0] for p in piece) - 2
        for p in inner:
            if p[0] == fx and p[1] % 2 == 0:
                g[p] = "s"
    elif name == "scrap_plate":  # rivets and rust patches on mismatched plates
        for p in rnd.sample(inner, min(len(inner), 3)):
            g[p] = "w"
        for p in rnd.sample(inner, min(len(inner), 4)):
            g[p] = "r"
    elif name == "chain_cowl":  # chain links: a checker of bright and dark rings
        for p in inner:
            if (p[0] + p[1]) % 2 == 0:
                g[p] = "w" if g[p] in "wi" else "i"
    elif name == "bone_armor" and k == 0:  # rib bars with dark gaps
        for p in inner:
            if (p[1] - top) % 3 == 2:
                g[p] = "r"
    elif name == "shadow_iron_plate":  # a cold glint along the lit top and left edges, and a ridge
        for p in inner:
            if (p[0] - 1, p[1]) not in piece or (p[0], p[1] - 1) not in piece or g.get((p[0] - 1, p[1])) == "o" \
                    or g.get((p[0], p[1] - 1)) == "o":
                g[p] = "w" if g[p] == "x" else "i"
        if k == 0:  # a raised ridge down the middle of the breastplate
            mx = (min(p[0] for p in piece) + max(p[0] for p in piece)) // 2
            for p in inner:
                if p[0] == mx:
                    g[p] = "i"


os.makedirs("art/source/gear/armor", exist_ok=True)
for form in FORMS:
    P = json.load(open(f"art/source/skerbie/parts/{form}.json"))
    W, H = P["width"], P["height"]
    s = H / 64  # kid pieces are drawn smaller
    for name, pieces in ARMORS.items():
        anims = {}
        for anim, frames in P["animations"].items():
            out = []
            for i, fr in enumerate(frames):
                rnd = random.Random(f"{form}/{name}/{anim}/{i}")
                g, owner = {}, {}
                for k, (kind, t0, t1, mat, extra) in enumerate(pieces):
                    piece = region(fr["parts"], fr["joints"], s, kind, t0, t1, extra) - set(owner)
                    if not piece:
                        continue
                    pg = shade(piece, RAMP[mat])
                    for p in piece:  # outline where the piece ends
                        if any((p[0] + dx, p[1] + dy) not in piece for dx, dy in N4):
                            pg[p] = "o"
                    pattern(name, piece, pg, k, rnd)
                    for p, c in pg.items():
                        g[p], owner[p] = c, k
                out.append(["".join(g.get((x, y), ".") for x in range(W)) for y in range(H)])
            anims[anim] = out
        json.dump({"width": W, "height": H, "fps": 10, "palette": PAL, "dye_zones": {}, "attach": {},
                   "animations": anims}, open(f"art/source/gear/armor/{name}_{form}.json", "w"), indent=1)
    print(f"{form}: 6 armours x {len(P['animations'])} animations")
