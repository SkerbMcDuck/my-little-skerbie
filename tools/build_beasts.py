# Builds the Bar Brawl beasts (ART_BRIEF §8): summoned by the druid, fought 1v1 on the tavern floor.
# Usage: python tools/build_beasts.py [name ...]
#        then render each art/source/tavern/beasts/<beast>.json with tools/render.py
#
# Beasts are fantastical and deliberately unlike the raid enemies: warm amber eyes instead of
# sickly green, and creature shapes rather than armed fighters. The "windup tell" is an eye
# flash: the eyes burn white on its last frame (the player's cue to get ready to parry).
# Same house style as everything else: faceted shading lit from the top-left, dark outline
# with a rim light; they face right and the game flips them to face Skerbie.
# Shares the drawing helpers (Canvas, ik, polar...) with tools/build_enemies.py.
#
# Animations (ART_BRIEF §8): summon [4] (materialises out of the druid's light), idle [3],
# tell [3] (windup, eye flash), strike [3], feint [3] (starts the strike, pulls up short),
# staggered [3] (dazed after a perfect parry: eyes shut, swaying), hit [2] (flash),
# ko [4] (turns to light and poofs back into the druid's ring). Every beast is drawn from the
# shared pose table bpose(); summon and ko are made from its own frames by the light helpers.
import json, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_enemies import Canvas, R, ik, polar, lerp, rot, hsh  # noqa: E402

OUT = "art/source/tavern/beasts"
os.makedirs(OUT, exist_ok=True)
R.update({
    "boar":   ["#a8643a", "#7a5636", "#3b2a22", "#17151c"],
    "snout":  ["#ffc8a8", "#f2a0b0", "#4a3a5c", "#2a2036"],
    "hoof":   ["#33303d", "#23212b", "#17151c", "#17151c"],
    "beye":   ["#ffd08a", "#ffb35c", "#ffb35c", "#ffb35c"],
    "tell":   ["#ffffff", "#fff4b0", "#fff4b0", "#fff4b0"],
    "light":  ["#ffffff", "#e4f27a", "#c8e04a", "#557a5c"],          # the druid's summoning light
    "yfur":   ["#f2f9ff", "#cfe9ff", "#9fc9f0", "#4d5e7a"],          # frost yeti fur
    "yarm":   ["#f2f9ff", "#cfe9ff", "#9fc9f0", "#4d5e7a"],
    "yskin":  ["#4d5e7a", "#3b4a63", "#2a3448", "#17151c"],
    "ice":    ["#f2f9ff", "#8ff0e6", "#2ec4b6", "#178f86"],
    "storm":  ["#5a5e66", "#3b4a63", "#2a3448", "#17151c"],          # thunder ox hide
    "cloud":  ["#5a5e66", "#33303d", "#23212b", "#17151c"],
    "bolt":   ["#ffffff", "#fff4b0", "#ffe14d", "#ffe14d"],
    "stone":  ["#8a8494", "#615b6b", "#433e4c", "#23212b"],          # moss golem
    "stone2": ["#8a8494", "#615b6b", "#433e4c", "#23212b"],
    "scale":  ["#4a3a5c", "#33303d", "#23212b", "#17151c"],          # ember wyrm
    "ember":  ["#ffe08a", "#ffb347", "#ff7a1a", "#c2410c"],
})


def bpose(anim, f):
    P = dict(anim=anim, f=f, bob=0, lean=0, head=0, crouch=0, tell=False, sway=0, legs=(0, 0, 0, 0),
             mouth=0, flash=False, daze=False, arm=0)
    if anim in ("idle", "summon"):
        f = f % 3
        P.update(bob=(0, -1, 0)[f], head=(0, -1, 1)[f], sway=(0, 1, 0)[f])
    elif anim == "tell":    # windup tell: drops its head, paws the floor, eyes flash on the last frame
        P.update([dict(lean=-1, head=1, crouch=1, arm=.5, legs=(0, 0, -2, 0)),
                  dict(lean=-2, head=2, crouch=2, arm=.85, legs=(0, -2, 0, 0)),
                  dict(lean=-2, head=3, crouch=2, arm=1, tell=True, legs=(0, 0, -2, 0))][f])
    elif anim == "strike":  # the real attack: a lunge forward
        P.update([dict(lean=3, head=2, crouch=1, arm=1.5, mouth=1, legs=(2, 1, 0, -1)),
                  dict(lean=6, head=2, crouch=1, arm=2, mouth=1, legs=(4, 2, -1, -2)),
                  dict(lean=2, head=1, arm=.5, legs=(2, 1, 0, 0))][f])
    elif anim == "feint":   # starts the same lunge, stops short and snorts
        P.update([dict(lean=2, head=2, crouch=1, arm=1.3, legs=(1, 0, 0, -1)),
                  dict(lean=0, head=-1, arm=1, legs=(0, 0, 0, 0)),
                  dict(lean=-1, head=1, arm=.6, mouth=1, legs=(0, 0, -1, 0))][f])
    elif anim == "staggered":
        P.update([dict(lean=-3, head=3, daze=True, sway=1, arm=.2),
                  dict(lean=-1, head=4, daze=True, sway=-1, crouch=1, arm=.1),
                  dict(lean=-2, head=3, daze=True, sway=1, arm=.2)][f])
    elif anim == "hit":
        P.update([dict(lean=-3, head=-1, flash=True, mouth=1, arm=.3), dict(lean=-2, head=0, arm=.2)][f])
    elif anim == "ko":
        P.update(lean=-3, crouch=2, head=4, daze=True, arm=.1)
    return P


class Scaled(Canvas):
    # Draw in a beast's design coordinates and land scaled on the canvas: x' = x*k + dx,
    # with the ground row (G) fixed, so a beast can be sized up without redrawing it.
    def __init__(self, w, h, k, dx, G):
        super().__init__(w, h)
        self.k, self.dx, self.G = k, dx, G

    def tf(self, p):
        return (p[0] * self.k + self.dx, self.G - (self.G - p[1]) * self.k)

    def poly(self, pts, ramp, flat=None, dark=0):
        super().poly([self.tf(p) for p in pts], ramp, flat, dark)

    def blob(self, cx, cy, rx, ry, ramp, flat=None, dark=0):
        x, y = self.tf((cx, cy))
        super().blob(x, y, rx * self.k, ry * self.k, ramp, flat, dark)

    def stick(self, a, b, w0, w1, ramp, flat=None, dark=0):
        super().stick(self.tf(a), self.tf(b), w0 * self.k, w1 * self.k, ramp, flat, dark)

    def px(self, x, y, ramp, shade):
        super().px(*self.tf((x, y)), ramp, shade)

    def at(self, x, y):
        x, y = self.tf((x, y))
        return int(round(x)), int(round(y))


def eye(g, ex, ey, P, big=False, brow=True):
    # Amber eye (2x2 when big); white-hot with a halo on the tell frame; a shut slit when dazed.
    if P["daze"]:
        for k in range(-1, 3 + big):
            g[(ex + k, ey + (1 if k in (0, 1) else 0))] = ("o",)
        return
    ramp = "tell" if P["tell"] else "beye"
    cells = ((0, 0, 0), (1, 0, 1), (0, 1, 1), (1, 1, 1)) if big else ((0, 0, 0), (1, 0, 1))
    for dx, dy, sh in cells:
        g[(ex + dx, ey + dy)] = (ramp, sh)
    if P["tell"]:
        hh = 2 if big else 1
        for dx in (-1, 2):
            for dy in range(hh):
                g[(ex + dx, ey + dy)] = ("tell", 1)
        for dx in (0, 1):
            g[(ex + dx, ey - 1)] = ("tell", 1)
            g[(ex + dx, ey + hh)] = ("tell", 1)
    if brow:
        for k in range(-2, 4):
            g[(ex + k, ey - 2 - (1 if P["tell"] else 0) + (k + 2) // 2)] = ("o",)


def quad_legs(c, P, G, legs, ramp, hoof, near):
    # legs: [(top, foot_x, which, width_top, width_bottom)], drawn darker when not near.
    ox, by = P["lean"], P["bob"] + P["crouch"]
    for top, fx, which, w0, w1 in legs:
        ft = (fx + P["legs"][which] + P["lean"] * 0.3, G - 1)
        c.stick((top[0] + ox, top[1] + by), ft, w0, w1, ramp, dark=0 if near else 1)
        hw = w1 * 0.6
        c.poly([(ft[0] - hw, ft[1] - 3), (ft[0] + hw + 1, ft[1] - 3), (ft[0] + hw + 1, ft[1] + 1), (ft[0] - hw, ft[1] + 1)],
               hoof, dark=0 if near else 1)


# ============================================================================ BST-1 Bramble Boar
def bramble_boar(c, P):  # 72x64: a hulking, hunched boar, bramble crest with glowing thorn tips, huge tusks
    G = 63
    ox, by = P["lean"], P["bob"] + P["crouch"]
    hy = P["head"] + 3                                                          # head held low: always ready to charge
    T = lambda pts: [(x + ox, y + by) for x, y in pts]
    quad_legs(c, P, G, [((41, 47), 45, 1, 7, 5.5), ((15, 47), 12, 3, 7, 5.5)], "boar", "hoof", False)
    c.stick((10 + ox, 40 + by), (5 + ox, 37 + by - P["sway"]), 3, 2, "moss")             # vine tail
    c.stick((5 + ox, 37 + by - P["sway"]), (4 + ox, 42 + by), 2.4, 1.6, "moss")
    c.poly(T([(8, 47), (10, 38), (18, 31), (30, 22), (40, 17), (48, 21), (53, 33), (51, 48), (38, 53), (20, 53), (11, 51)]), "boar")
    for x in range(14, 50, 3):
        c.px(x + ox, 52 + by + (x % 2), "boar", 3)
    for pts in (((22, 30), (26, 41), (22, 52)), ((35, 22), (38, 37), (34, 52))):        # vines round the flank
        pts = T(pts)
        c.stick(pts[0], pts[1], 2.2, 2.2, "moss", dark=1)
        c.stick(pts[1], pts[2], 2.2, 2.2, "moss", dark=1)
        c.blob(pts[1][0] + 2, pts[1][1] - 1, 2, 1.4, "moss")
    quad_legs(c, P, G, [((46, 47), 51, 0, 8.5, 6.5), ((19, 48), 17, 2, 8.5, 6.5)], "boar", "hoof", True)
    H_ = lambda pts: [(x + ox * 1.4, y + by + hy) for x, y in pts]
    jaw = 3 if P["mouth"] else 0
    c.poly(H_([(46, 24), (40, 15), (50, 22)]), "boar")                                   # ear, pinned back
    c.poly(H_([(48, 46 + jaw), (57, 48 + jaw), (56, 52 + jaw), (49, 51 + jaw)]), "boar", dark=1)   # jaw
    c.poly(H_([(43, 24), (51, 25), (57, 32), (62, 41), (62, 48), (56, 51), (49, 48), (44, 39)]), "boar")
    c.poly(H_([(58, 39), (63.5, 40), (63.5, 50), (58.5, 50)]), "snout")
    for d, dk in ((-3, 1), (0, 0)):                                                      # huge curved tusks
        a, b, e, t = H_([(52 + d, 51 + jaw), (61 + d, 51 + jaw), (66 + d, 44 + jaw), (64.5 + d, 35 + jaw)])
        c.stick(a, b, 4.8, 4.2, "bone", dark=dk)
        c.stick(b, e, 4.2, 3.2, "bone", dark=dk)
        c.stick(e, t, 3.2, 1.2, "bone", dark=dk)
    c.tips = []
    sway = P["sway"]
    for i, (x, y) in enumerate(((13, 34), (20, 28), (27, 23), (34, 19), (41, 17), (46, 19))):
        x, y = x + ox, y + by
        for k, ln in ((-1, 7), (1, 9)):
            tip = polar((x, y - 1), -112 + k * 18 - sway * 5 - i * 2, ln + (i % 2) * 2)
            ang = math.atan2(tip[1] - y + 1, tip[0] - x)
            nx_, ny_ = -math.sin(ang) * 2.2, math.cos(ang) * 2.2
            c.poly([(x + nx_, y - 1 + ny_), (x - nx_, y - 1 - ny_), tip], "bone")
            c.tips.append(tip)
        c.blob(x, y, 4, 3.2, "moss", dark=(i % 2))
    for x, y in ((22, 26), (36, 19), (14, 33)):
        c.blob(x + ox, y + by, 1.8, 1.6, "fung")
    g = c.finish()
    for tip in c.tips:                                                                   # thorn tips glow amber
        x, y = c.at(*tip)
        if (x, y) in g or (x, y + 1) in g:
            g[(x, y)] = ("beye", 1)
    eye(g, *c.at(53 + ox * 1.4, 31 + by + hy), P, big=True)
    nx, ny = c.at(62.5 + ox * 1.4, 42 + by + hy)
    g[(nx, ny)] = ("snout", 3)
    g[(nx, ny + 3)] = ("snout", 3)
    return g


# ============================================================================ BST-2 Frost Yeti
def frost_yeti(c, P):  # 72x72: a shaggy ice-furred ape with crystal horns and shoulder shards, overhead slam
    G = 71
    ox, by = P["lean"], P["bob"] + P["crouch"] * 1.5
    T = lambda pts, k=1.0: [(x + ox * k, y + by) for x, y in pts]
    hip = (30 + ox * 0.5, 47 + by)
    sh, sh2 = (42 + ox, 27 + by), (32 + ox, 26 + by)
    swing = P["arm"]

    def fist_at(s, base):
        keys = [(7 - P["sway"], 33), (-6, -20), (17, 34)]
        i = 0 if s < 1 else 1
        t = min(1, s - i)
        a, b = keys[i], keys[i + 1]
        return (base[0] + a[0] + (b[0] - a[0]) * t, base[1] + a[1] + (b[1] - a[1]) * t)

    # far arm, far leg
    f2 = fist_at(swing, sh2)
    f2 = (f2[0] - 3, min(G - 4, f2[1]))
    e2 = ik(sh2, f2, 15, 15, bend=-1)
    c.stick(sh2, e2, 9, 8, "yarm", dark=1)
    c.stick(e2, f2, 8, 6, "yarm", dark=1)
    c.blob(f2[0], f2[1], 4.5, 4, "yskin", dark=1)
    ff = (25 + P["legs"][3], G - 1)
    c.stick(hip, ff, 11, 9, "yfur", dark=1)
    c.poly([(ff[0] - 4, ff[1] - 3), (ff[0] + 6, ff[1] - 3), (ff[0] + 6, ff[1] + 1), (ff[0] - 4, ff[1] + 1)], "yskin", dark=1)
    # shaggy body, hunched, with a jagged fringe
    c.poly(T([(14, 50), (42, 52), (49, 40), (47, 24), (36, 14), (22, 17), (13, 30)]), "yfur")
    for x in range(14, 46, 4):                                                           # fringe along the bottom
        c.poly(T([(x, 49), (x + 4, 50), (x + 1.5, 55 + (x % 3))]), "yfur")
    for y in range(20, 48, 5):                                                           # fringe up the back
        c.poly(T([(15, y), (15, y + 5), (9 - (y % 2) * 2, y + 1)]), "yfur")
    for pts in (((29, 18), (22, 2), (34, 15)), ((36, 16), (36, 0), (42, 16)), ((22, 22), (12, 10), (28, 20)),
                ((42, 20), (46, 8), (47, 22))):
        c.poly(T(pts), "ice")                                                            # ice shards on the shoulders
    nf = (37 + P["legs"][0], G - 1)
    c.stick((hip[0] + 4, hip[1]), nf, 12, 10, "yfur")
    c.poly([(nf[0] - 4, nf[1] - 3), (nf[0] + 7, nf[1] - 3), (nf[0] + 7, nf[1] + 1), (nf[0] - 4, nf[1] + 1)], "yskin")
    # head: low on the hunched shoulders, a slate face inside a fur hood, curling crystal horns
    hx, hy = 50 + ox * 1.3, 22 + by + P["head"] * 0.6
    c.stick((hx - 4, hy - 6), (hx - 9, hy - 15), 5, 3.6, "ice")
    c.stick((hx - 9, hy - 15), (hx - 17, hy - 17), 3.6, 1.4, "ice")
    c.blob(hx - 2, hy - 1, 9.5, 8.5, "yfur")
    c.poly([(hx - 2, hy - 6), (hx + 6, hy - 6), (hx + 10, hy + 1), (hx + 9, hy + 7), (hx, hy + 8), (hx - 3, hy + 2)], "yskin")
    jaw = 2.5 if P["mouth"] else 0
    c.poly([(hx, hy + 5 + jaw), (hx + 7, hy + 5 + jaw), (hx + 6, hy + 8 + jaw), (hx + 1, hy + 8 + jaw)], "yskin", dark=1)
    # near arm: long, knuckles near the floor
    f1 = fist_at(swing, sh)
    f1 = (f1[0], min(G - 4, f1[1]))
    e1 = ik(sh, f1, 15, 15, bend=-1)
    c.stick(sh, e1, 10, 9, "yarm")
    c.stick(e1, f1, 9, 7, "yarm")
    c.blob(f1[0], f1[1], 5, 4.5, "yskin")
    g = c.finish()
    if P["mouth"]:                                                                      # fangs
        for x in (int(hx + 2), int(hx + 5)):
            g[(x, int(hy + 6 + jaw / 2))] = ("bone", 0)
    eye(g, int(round(hx + 3)), int(round(hy - 2)), P, big=True)
    return g


# ============================================================================ BST-3 Thunder Ox
def thunder_ox(c, P):  # 80x80: a storm bison, thundercloud mane crackling with lightning, horns tipped with sparks
    G = 79
    ox, by = P["lean"] * 1.2, P["bob"] + P["crouch"]
    T = lambda pts: [(x + ox, y + by) for x, y in pts]
    hy = P["head"] * 1.5 + 2
    quad_legs(c, P, G, [((52, 58), 56, 1, 9, 7), ((18, 58), 15, 3, 9, 7)], "storm", "hoof", False)
    c.stick((10 + ox, 44 + by), (4 + ox, 52 + by + P["sway"]), 2.6, 2, "storm")         # tail with a sparking tuft
    c.blob(4 + ox, 54 + by + P["sway"], 2.6, 3, "cloud")
    c.poly(T([(9, 56), (11, 42), (22, 32), (36, 25), (50, 22), (61, 28), (64, 42), (60, 60), (40, 63), (20, 63), (11, 60)]), "storm")
    nlegs = [((57, 58), 62, 0, 10, 8), ((22, 59), 21, 2, 10, 8)]
    quad_legs(c, P, G, nlegs, "storm", "hoof", True)
    clouds = [(16, 38, 6), (24, 31, 7.5), (33, 26, 8.5), (43, 23, 8.5), (52, 25, 7.5)]
    for i, (x, y, r) in enumerate(clouds):
        c.blob(x + ox, y + by - (P["sway"] if i % 2 else 0), r, r * 0.8, "cloud", dark=(i % 2))
    # head: a broad, low-slung skull with a pale muzzle; horns sweep out and forward
    H_ = lambda pts: [(x + ox * 1.3, y + by + hy) for x, y in pts]
    jaw = 3 if P["mouth"] else 0
    c.poly(H_([(62, 50 + jaw), (72, 52 + jaw), (71, 56 + jaw), (63, 55 + jaw)]), "storm", dark=1)
    c.poly(H_([(56, 30), (64, 29), (72, 38), (76, 48), (74, 54), (64, 55), (58, 46)]), "storm")
    c.poly(H_([(70, 44), (77, 47), (76, 55), (70, 55)]), "cloud")                        # muzzle
    c.poly(H_([(58, 33), (51, 29), (57, 36)]), "storm")                                  # ear
    for d, dk in ((-4, 1), (0, 0)):                                                      # horns: out, forward, up
        a, b, e = H_([(61 + d, 32), (53 + d, 25), (60 + d, 13)])
        c.stick(a, b, 6, 5, "bone", dark=dk)
        c.stick(b, e, 5, 1.6, "bone", dark=dk)
    g = c.finish()
    # lightning crackling through the mane (moves every frame) and sparking at the horn tips
    seed = P["f"] + {"idle": 0, "tell": 10, "strike": 20, "feint": 30, "staggered": 40, "hit": 50, "ko": 60, "summon": 70}[P["anim"]]
    for i in range(2):
        x = 18 + ((i * 19 + seed * 11) % 32) + ox
        y = 20 + by + (i * 3) % 5
        for k in range(5):
            nx_ = x + (3 if k % 2 == 0 else -2)
            for t in range(4):
                px_ = int(round(x + (nx_ - x) * t / 3))
                py_ = int(round(y + 3 * t / 3))
                if (px_, py_) in g and g[(px_, py_)][0] == "cloud":
                    g[(px_, py_)] = ("bolt", 0 if t % 2 else 1)
            x, y = nx_, y + 3
    for d in (-3, 0):
        tx, ty = c.at(60 + d + ox * 1.3, 13 + by + hy)
        g[(tx, ty)] = ("bolt", 0)
        if P["tell"] or (P["anim"] == "strike"):
            for dx, dy in ((-1, -1), (1, -1), (0, -2)):
                g[(tx + dx, ty + dy)] = ("bolt", 1)
    eye(g, *c.at(65 + ox * 1.3, 37 + by + hy), P, big=True)
    nx, ny = c.at(75.5 + ox * 1.3, 49 + by + hy)
    g[(nx, ny)] = ("o",)
    return g


# ============================================================================ BST-4 Moss Golem
def moss_golem(c, P):  # 88x88: a mossy boulder giant with a glowing amber core, ferns and mushrooms, ground punch
    G = 87
    ox, by = P["lean"] * 1.3, P["bob"] + P["crouch"] * 1.5
    T = lambda pts: [(x + ox, y + by) for x, y in pts]
    swing = P["arm"]
    hip = (38 + ox * 0.5, 62 + by)
    sh, sh2 = (58 + ox, 32 + by), (40 + ox, 30 + by)

    def fist_at(s, base):
        keys = [(8 - P["sway"], 38), (-8, -24), (18, 46)]
        i = 0 if s < 1 else 1
        t = min(1, s - i)
        a, b = keys[i], keys[i + 1]
        return (base[0] + a[0] + (b[0] - a[0]) * t, min(G - 7, base[1] + a[1] + (b[1] - a[1]) * t))

    f2 = fist_at(swing, sh2)
    f2 = (f2[0] - 4, f2[1])
    e2 = ik(sh2, f2, 18, 18, bend=-1)
    for a, b, r in ((sh2, e2, 7), (e2, f2, 6.5)):
        c.stick(a, b, r * 1.6, r * 1.5, "stone2", dark=1)
    c.blob(f2[0], f2[1], 8, 7.5, "stone2", dark=1)
    ff = (30 + P["legs"][3], G - 1)
    c.stick(hip, ff, 14, 13, "stone", dark=1)
    c.blob(ff[0] + 2, ff[1] - 3, 8, 4.5, "stone", dark=1)
    # boulder torso, moss on top, glowing cracks in the chest, ferns and mushrooms
    c.poly(T([(20, 64), (58, 64), (66, 50), (64, 30), (52, 18), (34, 18), (20, 30), (15, 48)]), "stone")
    for x, y, rx in ((26, 24, 10), (40, 18, 11), (54, 22, 9), (20, 36, 6), (62, 32, 5)):
        c.blob(x + ox, y + by, rx, rx * 0.55, "moss", dark=(x % 2))
    for x, y, a in ((30, 16, -100), (34, 15, -80), (46, 13, -95), (50, 14, -70), (22, 22, -120)):
        tip = polar((x + ox, y + by), a + P["sway"] * 4, 9)
        c.stick((x + ox, y + by), tip, 2.4, 1, "moss")
        mid = lerp((x + ox, y + by), tip, 0.5)
        c.stick(mid, polar(mid, a + 50, 3), 1.6, 1, "moss")
        c.stick(mid, polar(mid, a - 50, 3), 1.6, 1, "moss")
    for x, y in ((24, 30), (60, 26)):
        c.stick((x + ox, y + by + 1), (x + ox, y + by + 4), 1.6, 1.6, "bone")
        c.blob(x + ox, y + by, 2.6, 1.8, "fung")
    nf = (46 + P["legs"][0], G - 1)
    c.stick((hip[0] + 6, hip[1]), nf, 15, 14, "stone")
    c.blob(nf[0] + 2, nf[1] - 3, 9, 4.5, "stone")
    f1 = fist_at(swing, sh)
    e1 = ik(sh, f1, 18, 18, bend=-1)
    c.blob(sh[0] - 2, sh[1] - 2, 10, 8, "stone2")
    c.blob(sh[0] - 3, sh[1] - 7, 8, 3.5, "moss")
    # head: a stone block jutting forward over the shoulder, a moss beard
    hx, hy = 71 + ox * 1.2, 22 + by + P["head"] * 0.6
    c.poly([(hx - 8, hy - 7), (hx + 4, hy - 8), (hx + 9, hy - 2), (hx + 8, hy + 7), (hx - 7, hy + 8)], "stone")
    c.blob(hx - 3, hy - 7, 6, 2.4, "moss")
    for x in range(int(hx - 5), int(hx + 8), 3):
        c.poly([(x - 1.6, hy + 6), (x + 1.6, hy + 6), (x, hy + 13 + (x % 3))], "moss")
    for a, b, r in ((sh, e1, 7.5), (e1, f1, 7)):
        c.stick(a, b, r * 1.6, r * 1.5, "stone2")
    c.blob(f1[0], f1[1], 9, 8.5, "stone2")
    g = c.finish()
    core = []
    for (ax, ay), (bx, bb) in (((40, 42), (36, 34)), ((40, 42), (47, 36)), ((40, 42), (37, 52)), ((40, 42), (46, 50)),
                               ((36, 34), (32, 30)), ((47, 36), (52, 33)), ((37, 52), (32, 55))):
        for t in range(9):
            core.append((ax + (bx - ax) * t / 8, ay + (bb - ay) * t / 8))
    lit = 0 if (P["tell"] or P["anim"] == "strike") else 1
    for x, y in core:
        g[(int(x + ox), int(y + by))] = ("beye", lit)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            g[(int(40 + dx + ox), int(42 + dy + by))] = ("tell" if P["tell"] else "beye", 0 if dx == dy == 0 else 1)
    ex, ey = int(round(hx + 2)), int(round(hy))
    if P["daze"]:
        for k in range(-1, 4):
            g[(ex + k, ey + 1)] = ("o",)
    else:
        for x in range(ex - 3, ex + 5):
            g[(x, ey)] = ("o",)
        eye(g, ex, ey, P, big=False, brow=False)
        g[(ex + 2, ey)] = ("tell" if P["tell"] else "beye", 1)
    return g


# ============================================================================ BST-5 Ember Wyrm
def ember_wyrm(c, P):  # 96x96: a coiled serpent-dragon, charcoal scales split by glowing ember seams, lunging bite
    G = 95
    ox, by = P["lean"] * 1.6, P["bob"] + P["crouch"]
    hy = P["head"] * 1.2
    # the coil: from the tail tip, a loop on the floor, then the neck rearing high
    path = [(4, 90), (12, 92), (24, 92), (38, 90), (50, 85), (56, 76), (53, 66), (42, 61), (30, 64), (25, 73),
            (30, 82), (44, 84), (58, 80), (66, 70), (69, 56), (70, 42), (71, 30)]
    path = [(x, y + by * (0.2 if i < 11 else 1)) for i, (x, y) in enumerate(path)]
    neck_end = (73 + ox, 24 + by + hy)
    path[-1] = lerp(path[-2], neck_end, 0.5)
    path.append(neck_end)
    radii = [2.5, 4, 5, 6.5, 7.5, 8, 8, 8, 8.5, 9, 9.5, 9.5, 9.5, 9, 8.5, 8, 7.5, 7]
    belly, seams, c.tips = [], [], []
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        far = 4 <= i <= 9
        c.stick(a, b, radii[i] * 2, radii[i + 1] * 2, "scale", dark=1 if far else 0)
        c.blob(b[0], b[1], radii[i + 1], radii[i + 1], "scale", dark=1 if far else 0)
        d = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        if i >= 11:                                                                       # belly strip up the neck
            belly.append((polar(a, d + 90, radii[i] * 0.55), polar(b, d + 90, radii[i + 1] * 0.55), radii[i] * 0.9))
        if i >= 1 and not far:
            seams.append((b, d, radii[i + 1]))
        if i % 2 == 0 and i >= 2:                                                         # dorsal spines
            base = polar(b, d - 90, radii[i + 1] * 0.8)
            tip = polar(base, d - 110, 5 + radii[i + 1] * 0.5)
            c.poly([polar(base, d, 2.2), polar(base, d + 180, 2.2), tip], "bone")
            c.tips.append(tip)
    for a, b, w in belly:
        c.stick(a, b, w, w, "rust")
    for fx, dk in ((58, 1), (64, 0)):                                                    # small clawed forelegs
        sh = (fx + ox * 0.4, 70 + by)
        ft = (fx + 7 + P["legs"][0], 82 + by * 0.2)
        c.stick(sh, ft, 5, 3.6, "scale", dark=dk)
        for a in (10, 40, 70):
            c.stick(ft, polar(ft, a, 3.5), 1.8, 1, "bone", dark=dk)
    # head, drawn 1.4x around its own origin: a horned wedge with a frill; the jaw drops in the bite
    hx, hy0 = 75 + ox, 20 + by + hy
    S = lambda pts: [(hx + (x - hx) * 1.4, hy0 + (y - hy0) * 1.4) for x, y in pts]
    jaw = 22 if P["mouth"] else 4
    J = rot([(-2, 4), (13, 5), (12, 8), (-1, 9)], (hx - 2, hy0 + 4), jaw)
    c.poly(S(J), "scale", dark=1)
    for k in range(4):                                                                   # frill spikes
        c.poly(S([(hx - 6, hy0 - 2 + k * 3), (hx - 6, hy0 + 1 + k * 3), (hx - 13 - k, hy0 - 4 + k * 4)]), "rust")
    c.poly(S([(hx - 7, hy0 - 4), (hx + 4, hy0 - 6), (hx + 15, hy0), (hx + 16, hy0 + 4), (hx, hy0 + 5), (hx - 7, hy0 + 3)]), "scale")
    for d, dk in ((-2, 1), (1, 0)):                                                       # swept horns
        a, b = S([(hx - 2 + d, hy0 - 4), (hx - 11 + d, hy0 - 12)])
        c.stick(a, b, 3.6, 1.2, "bone", dark=dk)
    g = c.finish()
    hot = P["tell"] or P["anim"] == "strike"
    for b, d, r in seams:                                                                # glowing seams between scale rings
        for t in range(-int(r * 0.7), int(r * 0.7) + 1):
            p = polar(b, d + 90, t)
            q = (int(round(p[0])), int(round(p[1])))
            if q in g and g[q][0] == "scale":
                g[q] = ("ember", (1 if hot else 2) if abs(t) < r * 0.4 else 3)
    if P["mouth"]:                                                                       # fire in the throat, fangs
        mx, my = hx + 2 * 1.4, hy0 + 5.5 * 1.4
        for t in range(0, 15):
            x = int(round(hx + t * 1.2))
            y = int(round(my + t * 0.25))
            if (x, y) in g:
                g[(x, y)] = ("ember", 0 if hot else 1)
            if t % 4 == 1:
                g[(x, y - 1)] = ("bone", 0)
    for tip in c.tips:
        x, y = int(round(tip[0])), int(round(tip[1]))
        if (x, y) in g:
            g[(x, y)] = ("ember", 1)
    eye(g, int(round(hx + 3 * 1.4)), int(round(hy0 - 2.5 * 1.4)), P, big=True)
    g[(int(hx + 14.5 * 1.4), int(hy0 + 1 * 1.4))] = ("o",)
    return g


BEASTS = {  # name: (w, h, scale, x offset, builder)
    "bramble_boar": (72, 64, 1.06, 0, bramble_boar),
    "frost_yeti":   (72, 72, 1.0, 0, frost_yeti),
    "thunder_ox":   (80, 80, 1.0, 0, thunder_ox),
    "moss_golem":   (88, 88, 1.0, 0, moss_golem),
    "ember_wyrm":   (96, 96, 1.0, 0, ember_wyrm),
}
ANIMS = {"summon": 4, "idle": 3, "tell": 3, "strike": 3, "feint": 3, "staggered": 3, "hit": 2, "ko": 4}


def lit(g, amount, seed):
    # Part of the body turned to the druid's light: amount 0..1 of pixels become light.
    out = {}
    for (x, y), t in g.items():
        r = hsh(x, y, seed)
        if r < amount:
            out[(x, y)] = ("light", 0 if r < amount * 0.4 else 1)
        else:
            out[(x, y)] = t
    return out


def sparkle(g, w, h, n, spread, seed, keep):
    # A loose cloud of light motes around (and drifting up from) the body; keep = fraction of body kept.
    pts = list(g)
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    out = {p: t for p, t in g.items() if hsh(*p, seed + 1) < keep}
    for p in pts:
        if hsh(*p, seed) < n:
            x = int(round(p[0] + (p[0] - cx) * spread))
            y = int(round(p[1] + (p[1] - cy) * spread - spread * 14))
            if 0 <= x < w and 0 <= y < h:
                out[(x, y)] = ("light", 0 if hsh(x, y, 3) < 0.5 else 1)
    return out


def build(name):
    w, h, k, dx, fn = BEASTS[name]
    draw = lambda a, f: fn(Scaled(w, h, k, dx, h - 1), bpose(a, f))
    anims = {}
    idle0 = draw("idle", 0)
    # summon: motes gather, a light silhouette, the body lit through, then solid
    anims["summon"] = [sparkle(idle0, w, h, 0.05, 0.5, 1, 0.0),
                       {p: ("light", 1 if hsh(*p, 2) < 0.7 else 0) for p in idle0},
                       lit(idle0, 0.55, 4),
                       lit(idle0, 0.12, 5)]
    for a, n in ANIMS.items():
        if a in ("summon", "ko"):
            continue
        frames = []
        for f in range(n):
            g = draw(a, f)
            if bpose(a, f)["flash"]:
                g = {p: (t if t[0] in ("o", "beye", "tell", "bolt", "ember") else (t[0], 0)) for p, t in g.items()}
            frames.append(g)
        anims[a] = frames
    ko0 = draw("ko", 0)
    anims["ko"] = [ko0, lit(ko0, 0.6, 7), {p: ("light", 1) for p in ko0 if hsh(*p, 8) < 0.6},
                   sparkle(ko0, w, h, 0.06, 0.6, 9, 0.0)]
    write(name, w, h, anims)


def write(name, w, h, anims):
    from build_enemies import colour
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
    json.dump({"width": w, "height": h, "fps": 8, "palette": pal, "dye_zones": {}, "attach": {},
               "animations": grids}, open(f"{OUT}/{name}.json", "w"))
    print("wrote", name)


if __name__ == "__main__":
    for nm in [a for a in sys.argv[1:] if not a.startswith("-")] or list(BEASTS):
        build(nm)
