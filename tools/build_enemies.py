# Builds the enemies (ART_BRIEF §7): Gloomlings, Thornback bandits and the Hollow,
# three roles each (grunt / skirmisher / brute) plus a boss.
# Usage: python tools/build_enemies.py [name ...]
#        then render each art/source/enemies/<enemy>.json with tools/render.py
#
# Enemies face right like everything else (the game flips them to face Skerbie).
# Same house style as Skerbie: flat faceted shading lit from the top-left, dark outline
# with a rim light just inside it on the lit side. Eyes are sickly yellow-green.
# Red is used only for the attack-warning flash: on the last windup frame (and the boss
# special's warning frame) the whole outline turns red.
#
# Animations: walk [4], windup [2], strike [3], hit [2], defeat [4]; bosses add roar [4] and
# special [6]. Every enemy is drawn from one shared set of poses (pose()), so they move alike.
# Defeats are per family: Gloomlings burst into leaves, Thornbacks drop their gear and flee
# (root_dx in "attach" says how far the game slides them, in the drawn right-facing space),
# the Hollow dissolve into black smoke.
#
# Elemental variants are palette swaps. Each enemy has one "element zone" drawn with the
# reserved characters 1 2 3 4 (highlight -> deep); "element_ramps" lists the ice, fire,
# water and lightning ramps to swap in. The game adds the matching elemental aura effect.
#
# Boss special attacks have a separate effect sprite (<boss>_special_fx.json, 6 frames,
# drawn in a wider canvas whose top-left sits on the boss sprite's top-left: "anchor" [0, 0]).
# The sling runner's stone is its own small sprite (sling_stone.json); "release" in the
# strike attach data is where the game spawns it.
import json, math, os, sys

OUT = "art/source/enemies"
os.makedirs(OUT, exist_ok=True)
OUTLINE, WARN = "#0f0d14", "#ff3d3d"
R = {  # highlight, base, shadow, deep
    "wood":  ["#a8945e", "#7a5636", "#3b2a22", "#17151c"],
    "bone":  ["#bfae8c", "#a8945e", "#8b7a4a", "#3b2a22"],
    "moss":  ["#557a5c", "#3e5a46", "#2c4234", "#1f3d44"],
    "skin":  ["#a8945e", "#8b7a4a", "#5f7a3a", "#2c4234"],
    "iron":  ["#c9cfd6", "#5a5e66", "#33303d", "#17151c"],
    "rust":  ["#a8643a", "#7a5636", "#3b2a22", "#17151c"],
    "leath": ["#7a5636", "#3b2a22", "#23212b", "#17151c"],
    "plate": ["#4d5e7a", "#2a3448", "#23212b", "#17151c"],
    "cloak": ["#4a3a5c", "#3a2d4a", "#2a2036", "#17151c"],
    "rag":   ["#4a3a5c", "#3a2d4a", "#2a2036", "#17151c"],
    "hide":  ["#4a3a5c", "#33303d", "#23212b", "#17151c"],
    "rock":  ["#4d5e7a", "#3b4a63", "#2a3448", "#17151c"],
    "fung":  ["#ffc8a8", "#f2a0b0", "#4a3a5c", "#2a2036"],
    "smoke": ["#33303d", "#23212b", "#17151c", "#17151c"],
    "eye":   ["#e4f27a", "#c8e04a", "#c8e04a", "#c8e04a"],
    "spore": ["#e4f27a", "#c8e04a", "#557a5c", "#2c4234"],
    "dust":  ["#bfae8c", "#a8945e", "#8b7a4a", "#5f7a3a"],
}
ELEMENT_RAMPS = {
    "ice":       ["#f2f9ff", "#cfe9ff", "#9fc9f0", "#4d5e7a"],
    "fire":      ["#ffe08a", "#ffb347", "#ff7a1a", "#c2410c"],
    "water":     ["#8ff0e6", "#2ec4b6", "#178f86", "#1f3d44"],
    "lightning": ["#fff4b0", "#ffe14d", "#a8945e", "#33303d"],
}
LX, LY = -0.6, -0.8
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def inside(poly, x, y):
    px, py, hit = x + .5, y + .5, False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[i - 1]
        if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


class Canvas:
    # Every pixel holds a token (ramp, shade) so the element zone can get reserved characters.
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.t, self.part = {}, {}
        self.n = 0

    def _paint(self, pts, ramp, flat=None, dark=0):
        if not pts:
            return
        self.n += 1
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        cx, cy = (min(xs) + max(xs) + 1) / 2, (min(ys) + max(ys) + 1) / 2
        hw, hh = max(1, (max(xs) - min(xs) + 1) / 2), max(1, (max(ys) - min(ys) + 1) / 2)
        for (x, y) in pts:
            if 0 <= x < self.w and 0 <= y < self.h:
                lit = (x + .5 - cx) / hw * LX + (y + .5 - cy) / hh * LY
                s = flat if flat is not None else 0 if lit > 0.5 else 1 if lit > -0.15 else 2 if lit > -0.55 else 3
                self.t[(x, y)], self.part[(x, y)] = (ramp, min(3, s + dark)), self.n

    def poly(self, pts, ramp, flat=None, dark=0):
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        cells = [(x, y) for y in range(int(min(ys)) - 1, int(max(ys)) + 2)
                 for x in range(int(min(xs)) - 1, int(max(xs)) + 2) if inside(pts, x, y)]
        self._paint(cells, ramp, flat, dark)

    def blob(self, cx, cy, rx, ry, ramp, flat=None, dark=0):
        cells = [(x, y) for y in range(int(cy - ry) - 1, int(cy + ry) + 2)
                 for x in range(int(cx - rx) - 1, int(cx + rx) + 2)
                 if ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1]
        self._paint(cells, ramp, flat, dark)

    def stick(self, a, b, w0, w1, ramp, flat=None, dark=0):
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln, dx / ln
        self.poly([(a[0] + nx * w0 / 2, a[1] + ny * w0 / 2), (b[0] + nx * w1 / 2, b[1] + ny * w1 / 2),
                   (b[0] - nx * w1 / 2, b[1] - ny * w1 / 2), (a[0] - nx * w0 / 2, a[1] - ny * w0 / 2)],
                  ramp, flat, dark)

    def px(self, x, y, ramp, shade):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            self.t[(x, y)] = (ramp, shade)
            self.part.setdefault((x, y), self.n)

    def finish(self, warn=False):
        # A deep seam where a later part sits on an earlier one of another material, a rim light
        # just inside the outline on the lit side, then the outline itself.
        g = dict(self.t)
        for p, k in self.part.items():
            for dx, dy in N4:
                q = (p[0] + dx, p[1] + dy)
                if q in self.part and self.part[q] < k and self.t[q][0] != self.t[p][0] and self.t[p][0] != "eye":
                    g[p] = (self.t[p][0], 3)
                    break
        edge = {p for p in self.t if any((p[0] + dx, p[1] + dy) not in self.t for dx, dy in N4)}
        for (x, y), tok in self.t.items():
            if (x, y) not in edge and tok[0] != "eye" and ((x, y - 1) in edge or (x - 1, y) in edge):
                g[(x, y)] = (tok[0], max(0, g[(x, y)][1] - 1))
        for p in edge:
            g[p] = ("warn",) if warn else ("o",)
        return g


# ----------------------------------------------------------------------------- geometry helpers
def ik(hip, foot, l1, l2, bend=1):
    # Knee position for a two-bone limb; bend=+1 puts the knee forward (right).
    dx, dy = foot[0] - hip[0], foot[1] - hip[1]
    d = max(0.01, min(math.hypot(dx, dy), l1 + l2 - 0.01))
    a = math.acos(max(-1, min(1, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))))
    ang = math.atan2(dy, dx) - a * bend
    return (hip[0] + l1 * math.cos(ang), hip[1] + l1 * math.sin(ang))


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def polar(p, ang, ln):
    r = math.radians(ang)
    return (p[0] + ln * math.cos(r), p[1] + ln * math.sin(r))


def rot(pts, c, ang):
    r = math.radians(ang)
    co, si = math.cos(r), math.sin(r)
    return [(c[0] + x * co - y * si, c[1] + x * si + y * co) for x, y in pts]


def keyed(s, keys):
    # Interpolate a (dx, dy, angle) key for swing s: 0 = rest, 1 = cocked back, 2 = struck through.
    s = max(0.0, min(2.0, s))
    i = 0 if s < 1 else 1
    t = s - i
    a, b = keys[i], keys[i + 1]
    return tuple(a[j] + (b[j] - a[j]) * t for j in range(3))


def foot(P, which, bx, G, stride, lift):
    dx, up = P[which]
    return (bx + dx * stride, G - 1 - up * lift - P["air"])


def boot(c, f, ln, ramp, dark=0, ht=2.5):
    c.poly([(f[0] - ln * 0.35, f[1] - ht), (f[0] + ln * 0.65, f[1] - ht * 0.3), (f[0] + ln * 0.65, f[1] + 1),
            (f[0] - ln * 0.35, f[1] + 1)], ramp, dark=dark)


def thorns(c, pts, ramp="bone", size=1.0):
    # Back thorns: each point is a thorn base; they rake up and back.
    for i, (x, y) in enumerate(pts):
        s = size * (1 + 0.15 * (i % 2))
        c.poly([(x + 1.2 * s, y - 2 * s), (x + 2.5 * s, y + 2 * s), (x - 3.5 * s, y - 3 * s)], ramp)


# ----------------------------------------------------------------------------- shared poses
def pose(anim, f, special=None):
    P = dict(anim=anim, f=f, bob=0, lean=0, crouch=0, air=0, near=(0, 0), far=(0, 0), swing=0, sway=0,
             mouth=0, tilt=0, shake=0, flash=False, warn=False, flap=f % 2, gear="held", glow=0, plunge=0)
    if anim == "walk":
        p = f / 4 * 2 * math.pi
        P.update(near=(math.cos(p), 1 if f == 3 else 0), far=(-math.cos(p), 1 if f == 1 else 0),
                 bob=0 if f % 2 == 0 else -1, sway=math.cos(p))
    elif anim == "windup":
        P.update([dict(lean=-1, crouch=1, swing=.75, near=(.5, 0), far=(-.5, 0)),
                  dict(lean=-2, crouch=2, swing=1, near=(.5, 0), far=(-.5, 0), warn=True)][f])
    elif anim == "strike":
        P.update([dict(lean=1, crouch=1, swing=1.5, near=(1, 0), far=(-.5, 0), mouth=1),
                  dict(lean=3, crouch=2, swing=2, near=(1.2, 0), far=(-.7, 0), mouth=1),
                  dict(lean=1, crouch=1, swing=.4, near=(1, 0), far=(-.5, 0))][f])
    elif anim == "hit":
        P.update([dict(lean=-3, tilt=-1, swing=.3, flash=True, mouth=1), dict(lean=-2, crouch=1, swing=.2)][f])
    elif anim == "defeat":
        P.update(lean=-3, crouch=2, tilt=-1, swing=.3, mouth=1)
    elif anim == "roar":
        P.update([dict(crouch=2, lean=-1, swing=.5),
                  dict(crouch=-1, lean=-2, tilt=-2, mouth=1, swing=1),
                  dict(crouch=-1, lean=-2, tilt=-2, mouth=1, swing=1, shake=1),
                  dict(crouch=-1, lean=-2, tilt=-2, mouth=1, swing=1, shake=-1)][f])
    elif anim == "special":
        P.update(special[f])
    return P


# ============================================================================= GLOOMLINGS
def twig_imp(c, P):  # grunt, 24x24: a twig-and-moss pest with a claw swipe
    G = 23
    ox, oy = P["lean"] + P["shake"], P["bob"] + P["crouch"]
    hip = (11 + ox, 15 + oy)
    sh = (12 + ox * 1.5, 10 + oy)
    hx, hy = 13 + ox * 2, 6 + oy + P["tilt"]
    ff = foot(P, "far", 11, G, 3, 2)
    fk = ik(hip, ff, 4, 4.5)
    c.stick(hip, fk, 3, 3, "wood", dark=1)
    c.stick(fk, ff, 3, 3, "wood", dark=1)
    c.stick((sh[0] - 1, sh[1] + 1), (sh[0] - 2 - P["sway"] * 1.8, sh[1] + 6), 3, 2.6, "wood", dark=1)
    c.poly([(hip[0] - 2.5, hip[1] + 1), (hip[0] + 2.5, hip[1] + 1), (sh[0] + 2.5, sh[1]), (sh[0] - 2.5, sh[1] - 0.5)], "wood")
    c.blob(hip[0], hip[1] - 1, 3, 1.6, "moss")
    nf = foot(P, "near", 11, G, 3, 2)
    nk = ik(hip, nf, 4, 4.5)
    c.stick(hip, nk, 3, 3, "wood")
    c.stick(nk, nf, 3, 3, "wood")
    c.poly([(nf[0] - 1, nf[1] - 1), (nf[0] + 2.5, nf[1] + 0.5), (nf[0] - 1, nf[1] + 1.2)], "wood")
    c.stick((hx - 3, hy - 2), (hx - 7, hy - 5), 2.6, 1.6, "wood")
    c.stick((hx - 1, hy - 3), (hx - 4, hy - 6.5), 2.6, 1.6, "wood")
    c.blob(hx, hy + 0.5, 6, 5, "moss")
    for dx, ht in ((-4.5, 2.5), (-1.5, 3.5), (1.5, 2.5)):
        c.poly([(hx + dx - 1.8, hy - 3.5), (hx + dx + 1.8, hy - 4), (hx + dx - 0.5, hy - 3.5 - ht)], "moss")
    c.poly([(hx + 4.5, hy - 0.5), (hx + 9.5, hy + 1.5), (hx + 4.5, hy + 3)], "wood")
    dx, dy, ang = keyed(P["swing"], [(1 - P["sway"] * 2, 6, 60), (-4, -7, -120), (7, 2, 10)])
    hand = (sh[0] + dx, sh[1] + dy)
    c.stick(sh, hand, 3, 2.6, "wood")
    c.blob(sh[0], sh[1], 2, 1.6, "moss")
    c.stick(hand, polar(hand, ang, 2.5), 1.8, 1.2, "bone")
    g = c.finish(P["warn"])
    ex, ey = int(round(hx + 1)), int(round(hy - 1))
    for (x, y), s in (((ex, ey), 0), ((ex + 1, ey), 1), ((ex, ey + 1), 1), ((ex + 1, ey + 1), 1)):
        g[(x, y)] = ("eye", s)
    for x in range(ex, ex + 4):
        g[(x, ey + 3 + (1 if P["mouth"] and x > ex else 0))] = ("o",)
    g[(ex + 1, ey + 2)] = ("bone", 0)
    return g


def leaf_darter(c, P):  # skirmisher, 24x24: a hovering leaf with buzzing leaf wings and a thorn stinger
    cx = 11 + P["lean"] * 1.5 + P["shake"]
    cy = 11 + P["bob"] + P["crouch"] * 0.5 + (P["tilt"] * 0.5)
    ang = P["lean"] * 8 + P["tilt"] * 8
    C = (cx, cy)

    def R_(pts):
        return rot(pts, C, ang)

    wing_up = [(0, -2), (-4, -9), (-7, -8), (-3, -1.5)]
    wing_dn = [(0, -2), (-6, -5), (-9, -3), (-3, -1)]
    wing = wing_up if P["flap"] == 0 else wing_dn
    c.poly(R_([(x + 2, y) for x, y in wing]), "moss", dark=1)
    c.poly(R_([(-6, 0), (-11, -3), (-10, 0), (-12, 2), (-7, 1.5)]), "moss", dark=1)       # tail leaf
    for lx in (-1, 2):                                                                    # dangling twig feet
        a, b = R_([(lx, 2.5), (lx - 1, 6.5)])
        c.stick(a, b, 2.4, 2, "wood", dark=1)
    c.poly(R_([(-7, 0), (-3, -3.8), (4, -3.4), (8, -0.5), (4, 3.2), (-3, 3.4)]), "moss")
    c.poly(R_([(7, -1.2), (12.5, 0.2), (7, 1.4)]), "bone")                                 # stinger
    c.poly(R_(wing), "moss")
    for x in range(-5, 6):                                                                # leaf midrib
        mx, my = R_([(x, 0.6)])[0]
        c.px(mx, my, "moss", 3)
    g = c.finish(P["warn"])
    ex, ey = R_([(4, -1.5)])[0]
    ex, ey = int(round(ex)), int(round(ey))
    g[(ex, ey)] = ("eye", 0)
    g[(ex + 1, ey)] = ("eye", 1)
    g[(ex, ey + 1)] = ("eye", 1)
    return g


def mossy_lump(c, P):  # brute, 32x28: a walking mound of moss with rock fists and a slam
    G = 27
    ox, oy = P["lean"] + P["shake"], P["bob"] + P["crouch"]
    ff = foot(P, "far", 12, G, 2, 2)
    c.stick((13 + ox, 21 + oy), ff, 6, 5, "wood", dark=1)
    boot(c, ff, 6, "wood", dark=1)
    c.stick((12 + ox, 14 + oy), (9 + ox - P["sway"] * 2, 22 + oy), 5, 4.5, "moss", dark=1)
    c.blob(9 + ox - P["sway"] * 2, 23 + oy, 2.8, 2.5, "rock", dark=1)
    for pts in (((6, 11), (9, 5), (11, 12)), ((10, 7), (14, 1.5), (15, 9))):              # rock shards on its back
        c.poly([(x + ox, y + oy) for x, y in pts], "rock")
    c.blob(15 + ox, 16.5 + oy, 11, 9, "moss")
    for x, ln in ((18, 3.5), (21, 5), (24, 4), (26.5, 3)):                                # moss fringe over the face
        c.poly([(x + ox - 1.6, 10.5 + oy), (x + ox + 1.6, 10.5 + oy), (x + ox + 0.3, 10.5 + oy + ln)], "moss")
    nf = foot(P, "near", 18, G, 2, 2)
    c.stick((17 + ox, 21 + oy), nf, 6, 5, "wood")
    boot(c, nf, 6, "wood")
    sh = (19 + ox, 14 + oy)
    dx, dy, _ = keyed(P["swing"], [(4 - P["sway"] * 2, 9, 0), (-3, -9, 0), (9, 9, 0)])
    fist = (sh[0] + dx, sh[1] + dy)
    c.stick(sh, fist, 5.5, 4.5, "moss")
    c.blob(fist[0], fist[1], 3.2, 3, "rock")
    g = c.finish(P["warn"])
    ex, ey = int(round(23 + ox)), int(round(15 + oy + P["tilt"]))
    g[(ex, ey)] = ("eye", 0)
    g[(ex + 1, ey)] = ("eye", 1)
    g[(ex - 1, ey)] = ("o",)
    g[(ex + 2, ey)] = ("o",)
    my = ey + 4
    for x in range(ex - 1, ex + 4):
        g[(x, my)] = ("o",)
        if P["mouth"]:
            g[(x, my + 1)] = ("o",)
    g[(ex, my)] = ("bone", 0)
    g[(ex + 2, my)] = ("bone", 1)
    return g


MOTHER_SPECIAL = [dict(crouch=1, lean=-1, swing=.8),
                  dict(crouch=-1, lean=-2, swing=1, tilt=-1, warn=True),
                  dict(crouch=-1, lean=-2, swing=1, tilt=-1, glow=1, mouth=1),
                  dict(lean=2, crouch=2, swing=2, mouth=1, glow=1),
                  dict(lean=2, crouch=2, swing=2, mouth=1),
                  dict(lean=1, crouch=1, swing=1.6)]


def gloom_mother(c, P):  # boss, 48x44: a hunched moss matron, antler crown, glowing spore staff
    G = 51
    ox, oy = P["lean"] * 1.3 + P["shake"], P["bob"] + P["crouch"] * 1.3 + 8
    ff = foot(P, "far", 20, G, 3, 2)
    c.stick((20 + ox, 33 + oy), ff, 7, 6, "wood", dark=1)
    boot(c, ff, 8, "wood", dark=1, ht=3)
    sh2 = (19 + ox, 19 + oy)
    fh = (14 + ox - P["sway"] * 2, 31 + oy)
    c.stick(sh2, fh, 4.5, 3.5, "moss", dark=1)
    for a in (60, 90, 120):
        c.stick(fh, polar(fh, a, 3), 1.8, 1.2, "bone", dark=1)
    for x, y, r in ((9, 23, 3), (11, 16, 2.4), (7, 29, 2.2)):                             # mushrooms on her back
        c.stick((x + ox + 1, y + oy + 1), (x + ox + 2, y + oy + 4), 2, 2, "bone")
        c.blob(x + ox, y + oy, r, r * 0.7, "fung")
    c.poly([(x + ox, y + oy) for x, y in ((10, 36), (34, 36), (37, 26), (33, 15), (24, 10), (14, 12), (8, 23))], "moss")
    for x, ln in ((12, 4), (16, 6), (20, 4), (24, 6), (28, 4), (32, 5)):                  # shawl hem
        c.poly([(x + ox - 2, 35 + oy), (x + ox + 2, 35 + oy), (x + ox, 35 + oy + ln)], "moss")
    nf = foot(P, "near", 27, G, 3, 2)
    c.stick((27 + ox, 33 + oy), nf, 7, 6, "wood")
    boot(c, nf, 8, "wood", ht=3)
    hx, hy = 32 + ox * 1.3, 13 + oy + P["tilt"]
    for base, mid, tips in (((hx - 3, hy - 4), (hx - 7, hy - 11), ((hx - 11, hy - 13), (hx - 4, hy - 15))),
                            ((hx + 1, hy - 5), (hx + 3, hy - 11), ((hx + 7, hy - 13), (hx + 1, hy - 15)))):
        c.stick(base, mid, 3.2, 3, "wood")
        for t in tips:
            c.stick(mid, t, 3, 2.4, "wood")
    c.blob(hx, hy, 6.5, 6, "moss")
    c.poly([(hx + 4, hy - 0.5), (hx + 12, hy + 4), (hx + 10, hy + 5.5), (hx + 4, hy + 3)], "wood")
    for x, ln in ((hx - 4, 7), (hx - 1, 5), (hx + 2, 4)):                                  # drooping hair
        c.poly([(x - 1.8, hy - 3), (x + 1.8, hy - 3), (x, hy - 3 + ln)], "moss")
    sh = (30 + ox, 19 + oy)
    dx, dy, ang = keyed(P["swing"], [(9 - P["sway"] * 2, 10, -88), (2, -6, -125), (10, 5, 60)])
    fist = (sh[0] + dx, sh[1] + dy)
    top, bot = polar(fist, ang, 17), polar(fist, ang + 180, 10)
    c.stick(bot, top, 3, 3, "wood")
    c.stick(top, polar(top, ang + 70, 4), 2.8, 2.2, "wood")                                # crooked hook
    el = ik(sh, fist, 5.5, 6, bend=-1)
    c.stick(sh, el, 4.5, 4, "moss")
    c.stick(el, fist, 4, 3.5, "moss")
    c.blob(fist[0], fist[1], 2.4, 2.2, "moss")
    bulb = polar(top, ang + 70, 4.5)
    c.bulb = bulb
    g = c.finish(P["warn"])
    r = 1.6 + P["glow"] * 1.2
    for y in range(int(bulb[1] - r) - 1, int(bulb[1] + r) + 2):
        for x in range(int(bulb[0] - r) - 1, int(bulb[0] + r) + 2):
            d = math.hypot(x + .5 - bulb[0], y + 1.5 - bulb[1])
            if d <= r:
                g[(x, y + 1)] = ("eye", 0 if d < r * 0.5 else 1)
    for t in ((hx - 11, hy - 13), (hx - 4, hy - 15), (hx + 7, hy - 13), (hx + 1, hy - 15)):  # firefly lights on the antlers
        g[(int(round(t[0])), int(round(t[1])))] = ("eye", 0)
    ex, ey = int(round(hx + 2)), int(round(hy - 1))
    g[(ex, ey)] = ("eye", 0)
    g[(ex + 1, ey)] = ("eye", 1)
    for x in range(ex - 1, ex + 3):
        g[(x, ey - 1)] = ("o",)
    my = ey + 5
    for x in range(ex - 1, ex + 4):
        g[(x, my)] = ("o",)
        if P["mouth"]:
            g[(x, my + 1)] = ("o",)
            g[(x, my + 2)] = ("o",)
    if P["mouth"]:
        g[(ex, my + 1)] = ("bone", 0)
        g[(ex + 2, my + 2)] = ("bone", 1)
    return g


# ============================================================================= THORNBACKS
def club(c, fist, ang):
    tip = polar(fist, ang, 10)
    c.stick(polar(fist, ang + 180, 2), tip, 3, 5.5, "wood")
    for t in (0.6, 0.85):
        p = lerp(fist, tip, t)
        a, b = polar(p, ang - 90, 2.5), polar(p, ang + 90, 2.5)
        c.px(a[0], a[1], "bone", 0)
        c.px(b[0], b[1], "bone", 1)


def club_thug(c, P):  # grunt, 40x40: hunched scavenger, pot helmet, spiked club
    G = 39
    ox, by = P["lean"] + P["shake"], P["bob"] + P["crouch"]
    hip = (17 + ox, 28 + by)
    ff = foot(P, "far", 17, G, 4, 2)
    fk = ik(hip, ff, 6, 6)
    c.stick(hip, fk, 5, 4.5, "skin", dark=1)
    c.stick(fk, ff, 4.5, 4, "leath", dark=1)
    boot(c, ff, 6, "leath", dark=1)
    c.stick((20 + ox, 18 + by), (17 + ox - P["sway"], 27 + by), 4, 3.5, "skin", dark=1)
    thorns(c, [(13 + ox, 25 + by), (12 + ox, 21 + by), (13 + ox, 17 + by), (16 + ox, 14 + by)])
    c.poly([(x + ox, y + by) for x, y in ((12, 29), (23, 30), (27, 25), (26, 18), (20, 14), (14, 16), (11, 22))], "skin")
    c.poly([(x + ox, y + by) for x, y in ((19, 18), (26, 19), (27.5, 25), (24, 28), (18, 26))], "iron")
    for x, y in ((21, 20), (25, 21), (24, 26)):
        c.px(x + ox, y + by, "iron", 0)
    c.poly([(x + ox, y + by) for x, y in ((12, 27), (24, 28), (23.5, 30.5), (12, 30))], "leath")
    nf = foot(P, "near", 19, G, 4, 2)
    nk = ik(hip, nf, 6, 6)
    c.stick(hip, nk, 6, 5, "skin")
    c.stick(nk, nf, 5, 4.5, "leath")
    boot(c, nf, 7, "leath")
    hx, hy = 27 + ox * 1.5, 12 + by + P["tilt"]
    c.poly([(hx - 4, hy - 2), (hx - 13, hy - 7), (hx - 5, hy + 2)], "skin")
    c.blob(hx, hy, 5, 4.6, "skin")
    c.poly([(hx + 2.5, hy - 1.5), (hx + 9, hy + 2), (hx + 6, hy + 3.2), (hx + 3, hy + 2.5)], "skin")
    jaw = 1.5 if P["mouth"] else 0
    c.poly([(hx - 4, hy + 1.5 + jaw), (hx + 4.5, hy + 2.5 + jaw), (hx + 4, hy + 6 + jaw), (hx - 3, hy + 5.5 + jaw)], "skin")
    c.poly([(hx - 6, hy - 1), (hx - 5.5, hy - 4.5), (hx - 2, hy - 7), (hx + 2, hy - 7), (hx + 5, hy - 4), (hx + 5.5, hy - 1)], "iron")
    c.poly([(hx - 7, hy - 2), (hx + 6.5, hy - 2), (hx + 6.5, hy), (hx - 7, hy)], "rust")
    c.px(hx - 1, hy - 5, "iron", 3)
    c.px(hx + 1, hy - 1, "iron", 0)
    sh = (21 + ox, 19 + by)
    dx, dy, ang = keyed(P["swing"], [(4 + P["sway"] * 2, 8, 55), (-3 - ox, -11, -142), (10, 6, 60)])
    fist = (sh[0] + dx, sh[1] + dy)
    el = ik(sh, fist, 5, 5.5, bend=-1)
    if P["gear"] == "held":
        club(c, fist, ang)
    c.stick(sh, el, 5, 4.5, "skin")
    c.stick(el, fist, 4.5, 4, "skin")
    c.blob(fist[0], fist[1], 2.4, 2.2, "leath")
    g = c.finish(P["warn"])
    ex, ey = int(round(hx + 1)), int(round(hy - 1))
    g[(ex, ey)] = ("eye", 0)
    g[(ex + 1, ey)] = ("eye", 1)
    for x in range(ex - 1, ex + 3):
        g[(x, ey - 1)] = ("o",)
    for x in range(ex - 1, ex + 4):
        g[(x, ey + 4)] = ("o",)
        if P["mouth"]:
            g[(x, ey + 5)] = ("o",)
    g[(ex + 3, ey + 3)] = ("bone", 0)
    return g


def sling_runner(c, P):  # skirmisher, 36x40: a lanky runner, rag mask, whirling sling
    G = 39
    ox, by = P["lean"] + P["shake"], P["bob"] + P["crouch"]
    hip = (15 + ox, 25 + by)
    ff = foot(P, "far", 15, G, 5, 3)
    fk = ik(hip, ff, 7, 7.5)
    c.stick(hip, fk, 4, 3.5, "skin", dark=1)
    c.stick(fk, ff, 3.5, 3, "skin", dark=1)
    boot(c, ff, 5, "leath", dark=1, ht=2)
    c.stick((17 + ox, 16 + by), (14 + ox - P["sway"] * 2, 24 + by), 3, 2.6, "skin", dark=1)
    thorns(c, [(11 + ox, 21 + by), (11 + ox, 17 + by), (13 + ox, 14 + by)], size=0.8)
    c.poly([(x + ox, y + by) for x, y in ((11, 26), (19, 26), (21, 19), (19, 13), (13, 14), (10, 20))], "skin")
    c.poly([(x + ox, y + by) for x, y in ((12, 16), (20, 16), (20.5, 23), (12, 24.5))], "leath")
    c.poly([(x + ox, y + by) for x, y in ((11, 24), (20, 24), (19.5, 26.5), (11, 26.5))], "rag")
    nf = foot(P, "near", 17, G, 5, 3)
    nk = ik(hip, nf, 7, 7.5)
    c.stick(hip, nk, 4.5, 4, "skin")
    c.stick(nk, nf, 4, 3.5, "skin")
    boot(c, nf, 6, "leath", ht=2)
    hx, hy = 21 + ox * 1.5, 9 + by + P["tilt"]
    flut = (0, 1, 0, -1)[P["f"] % 4]
    c.poly([(hx - 3, hy + 1), (hx - 9, hy + 1 + flut), (hx - 8, hy + 3 + flut), (hx - 3, hy + 2.5)], "rag")
    c.poly([(hx - 2, hy - 2), (hx - 11, hy - 6), (hx - 2, hy + 1)], "skin")
    c.blob(hx, hy, 4, 3.8, "skin")
    c.poly([(hx + 2, hy - 1), (hx + 8, hy + 1), (hx + 6.5, hy + 3), (hx + 2, hy + 3)], "skin")
    c.poly([(hx - 1, hy + 0.5), (hx + 7.5, hy + 1.2), (hx + 6.5, hy + 3.4), (hx - 1, hy + 3.2)], "rag")
    sh = (18 + ox, 16 + by)
    dx, dy, ang = keyed(P["swing"], [(2 - P["sway"] * 2, 8, 100), (-1, -9, 270), (8, -2, 330)])
    fist = (sh[0] + dx, sh[1] + dy)
    el = ik(sh, fist, 4.5, 5, bend=-1)
    pouch = polar(fist, ang, 6)
    if P["gear"] == "held":
        for k in (-1, 1):
            a = polar(fist, ang + 90 * k, 0.6)
            for t in (0.25, 0.5, 0.75):
                p = lerp(a, pouch, t)
                c.px(p[0], p[1], "leath", 0)
    c.stick(sh, el, 3.5, 3, "skin")
    c.stick(el, fist, 3, 2.6, "skin")
    loaded = not (P["anim"] == "strike" and P["f"] >= 1)
    if P["gear"] == "held":
        c.blob(pouch[0], pouch[1], 1.8, 1.6, "leath")
    g = c.finish(P["warn"])
    if P["gear"] == "held" and loaded:
        g[(int(round(pouch[0])), int(round(pouch[1])))] = ("rock", 0)
    ex, ey = int(round(hx + 1)), int(round(hy - 1))
    g[(ex, ey)] = ("eye", 0)
    g[(ex + 1, ey)] = ("eye", 1)
    g[(ex - 1, ey - 1)] = ("o",)
    g[(ex, ey - 1)] = ("o",)
    c.release = pouch
    return g


def sling(c, fist, ang):  # the sling alone (dropped)
    pouch = polar(fist, ang, 6)
    c.stick(fist, pouch, 1.6, 1.6, "leath")
    c.blob(pouch[0], pouch[1], 1.8, 1.6, "leath")


def shield(c, ctr, ang, dark=0):
    pts = lambda P_: rot(P_, ctr, ang)
    c.poly(pts([(-4, -11), (4, -12), (4.5, 11), (-4, 12)]), "wood", dark=dark)
    for y in (-11.5, 9.5):
        c.poly(pts([(-4.5, y), (5, y - 0.3), (5, y + 2.2), (-4.5, y + 2.4)]), "iron", dark=dark)
    for x in (-1.3, 1.5):
        for y in range(-8, 9, 1):
            p = pts([(x, y)])[0]
            c.px(p[0], p[1], "wood", 3)
    c.poly(pts([(3, -2.5), (9, 0), (3, 2.5)]), "bone", dark=dark)
    c.blob(*pts([(2, 0)])[0], 2.6, 2.6, "iron", dark=dark)


def shield_brute(c, P):  # brute, 48x44: a hulk behind a plank-and-iron door shield, shield bash
    G = 43
    ox, by = P["lean"] * 1.2 + P["shake"], P["bob"] + P["crouch"]
    hip = (19 + ox, 30 + by)
    ff = foot(P, "far", 18, G, 4, 2)
    fk = ik(hip, ff, 6.5, 6.5)
    c.stick(hip, fk, 7, 6, "skin", dark=1)
    c.stick(fk, ff, 6, 5.5, "leath", dark=1)
    boot(c, ff, 8, "leath", dark=1, ht=3)
    thorns(c, [(12 + ox, 27 + by), (10 + ox, 22 + by), (11 + ox, 17 + by), (14 + ox, 13 + by), (18 + ox, 10.5 + by)], size=1.2)
    c.poly([(x + ox, y + by) for x, y in ((11, 31), (27, 31), (30, 24), (28, 15), (20, 11), (12, 14), (9, 22))], "skin")
    c.poly([(x + ox, y + by) for x, y in ((11, 28), (28, 28.5), (27.5, 31.5), (11, 31.5))], "leath")
    nf = foot(P, "near", 21, G, 4, 2)
    nk = ik(hip, nf, 6.5, 6.5)
    c.stick(hip, nk, 8, 7, "skin")
    c.stick(nk, nf, 7, 6, "leath")
    boot(c, nf, 9, "leath", ht=3)
    hx, hy = 27 + ox * 1.3, 11 + by + P["tilt"]
    c.blob(hx, hy, 4.5, 4, "skin")
    jaw = 1.5 if P["mouth"] else 0
    c.poly([(hx - 2, hy + 1 + jaw), (hx + 6, hy + 1.5 + jaw), (hx + 5.5, hy + 5 + jaw), (hx - 2, hy + 5 + jaw)], "skin")
    c.poly([(hx - 5, hy), (hx - 4, hy - 4), (hx, hy - 5.5), (hx + 4, hy - 4), (hx + 5, hy)], "iron")
    c.poly([(hx - 1, hy - 5), (hx + 1.5, hy - 5), (hx - 2, hy - 10)], "bone")
    sh = (25 + ox, 17 + by)
    dx, dy, ang = keyed(P["swing"], [(8 + P["sway"], 9, 0), (3, 6, -14), (14, 8, 4)])
    ctr = (sh[0] + dx, sh[1] + dy)
    c.stick(sh, (ctr[0] - 3, ctr[1]), 6, 5, "skin")
    if P["gear"] == "held":
        shield(c, ctr, ang)
    g = c.finish(P["warn"])
    ex, ey = int(round(hx + 1)), int(round(hy - 1))
    if (ex, ey) in g:
        g[(ex, ey)] = ("eye", 0)
        g[(ex + 1, ey)] = ("eye", 1)
    for x in range(ex - 1, ex + 3):
        if (x, ey - 1) in g:
            g[(x, ey - 1)] = ("o",)
    return g


CHIEF_SPECIAL = [dict(crouch=3, lean=-1, swing=.8),
                 dict(air=5, lean=-1, swing=1, warn=True, near=(.5, 1), far=(-.5, 1), mouth=1),
                 dict(air=4, lean=1, swing=1.5, near=(.8, 1), far=(-.3, 1), mouth=1),
                 dict(crouch=3, lean=3, swing=2, near=(1, 0), far=(-.6, 0), mouth=1),
                 dict(crouch=3, lean=3, swing=2, near=(1, 0), far=(-.6, 0), mouth=1, shake=1),
                 dict(crouch=1, lean=1, swing=1.2, near=(.8, 0), far=(-.4, 0))]


def cleaver(c, fist, ang):
    c.stick(polar(fist, ang + 180, 3), polar(fist, ang, 4), 2.6, 2.6, "leath")
    b0, b1 = polar(fist, ang, 4), polar(fist, ang, 20)
    n = ang - 90
    c.poly([polar(b0, n + 180, 1.5), polar(b1, n + 180, 1), polar(b1, n, 9), polar(polar(b0, ang, 3), n, 8.5), polar(b0, n, 3)], "iron")
    for t in (0.4, 0.75):
        p = polar(lerp(b0, b1, t), n, 4)
        c.px(p[0], p[1], "rust", 1)
    p = polar(lerp(b0, b1, 0.3), n, 1.5)
    c.px(p[0], p[1], "iron", 3)


def thornback_chief(c, P):  # boss, 56x64: a crowned bandit warlord, pelt mantle, great cleaver, leaping smash
    G = 63
    k = 1.3
    ox, by = P["lean"] * k + P["shake"], (P["bob"] + P["crouch"]) * k - P["air"]
    hip = (24 + ox, 44 + by)
    ff = foot(P, "far", 23, G, 5, 3)
    fk = ik(hip, ff, 8.5, 8.5)
    c.stick(hip, fk, 8, 7, "skin", dark=1)
    c.stick(fk, ff, 7, 6, "rust", dark=1)
    boot(c, ff, 9, "rust", dark=1, ht=3)
    c.stick((20 + ox, 27 + by), (18 + ox - P["sway"] * 2, 40 + by), 6, 5, "skin", dark=1)
    c.blob(18 + ox - P["sway"] * 2, 41 + by, 3, 3, "skin", dark=1)
    thorns(c, [(15 + ox, 34 + by), (13 + ox, 29 + by), (14 + ox, 24 + by)], size=1.6)
    c.poly([(x + ox, y + by) for x, y in ((19, 46), (30, 46), (33, 39), (38, 28), (33, 21), (20, 21), (14, 27), (17, 38))], "skin")
    for x, y in ((26, 29), (28, 32), (31, 29)):                                           # old scars
        c.px(x + ox, y + by, "skin", 3)
    c.poly([(x + ox, y + by) for x, y in ((17, 42), (31, 42), (30.5, 46), (18, 46))], "leath")
    c.blob(28 + ox, 44 + by, 2.6, 2.4, "bone")                                           # skull buckle
    mant = [(13, 30), (15, 22), (21, 18), (29, 18), (33, 21), (29, 23), (26, 22), (23, 26), (20, 24), (17, 29)]
    c.poly([(x + ox, y + by) for x, y in mant], "rust")
    nf = foot(P, "near", 26, G, 5, 3)
    nk = ik(hip, nf, 8.5, 8.5)
    c.stick(hip, nk, 9, 8, "skin")
    c.stick(nk, nf, 8, 7, "rust")
    boot(c, nf, 10, "rust", ht=3)
    hx, hy = 35 + ox * 1.3, 16 + by + P["tilt"]
    c.poly([(hx - 4, hy - 2), (hx - 15, hy - 7), (hx - 5, hy + 2)], "skin")
    c.blob(hx, hy, 6.5, 6, "skin")
    c.poly([(hx + 4, hy - 1.5), (hx + 12, hy + 2.5), (hx + 8.5, hy + 4), (hx + 4, hy + 3.5)], "skin")
    jaw = 2 if P["mouth"] else 0
    c.poly([(hx - 5, hy + 2.5 + jaw), (hx + 7, hy + 3.5 + jaw), (hx + 6.5, hy + 8 + jaw), (hx - 4, hy + 7.5 + jaw)], "skin")
    for i, (dx, ht) in enumerate(((-4.5, 5), (-1.5, 8), (1.5, 7), (4.2, 5))):             # crown of bone thorns
        c.poly([(hx + dx - 1.6, hy - 4.5), (hx + dx + 1.6, hy - 5), (hx + dx + 0.6, hy - 4.5 - ht)], "bone")
    c.poly([(hx - 6, hy - 3.5), (hx + 5.5, hy - 5.5), (hx + 6.2, hy - 3), (hx - 6, hy - 1.5)], "iron")
    sh = (32 + ox, 25 + by)
    dx, dy, ang = keyed(P["swing"], [(5 + P["sway"] * 2, 12, 60), (-4 - ox * 0.5, -14, -145), (12, 9, 55)])
    fist = (sh[0] + dx, sh[1] + dy)
    el = ik(sh, fist, 7, 7.5, bend=-1)
    if P["gear"] == "held":
        cleaver(c, fist, ang)
    c.stick(sh, el, 7, 6, "skin")
    c.stick(el, fist, 6, 5, "skin")
    c.blob(sh[0], sh[1] - 1, 4.5, 3.5, "rust")
    c.blob(fist[0], fist[1], 3, 2.8, "leath")
    g = c.finish(P["warn"])
    ex, ey = int(round(hx + 1)), int(round(hy - 1))
    g[(ex, ey)] = ("eye", 0)
    g[(ex + 1, ey)] = ("eye", 1)
    for x in range(ex - 1, ex + 3):
        g[(x, ey - 1)] = ("o",)
    g[(ex - 2, ey + 1)] = ("o",)                                                        # scar across the eye
    g[(ex - 1, ey + 2)] = ("o",)
    for x in range(ex - 1, ex + 5):
        g[(x, ey + 5)] = ("o",)
        if P["mouth"]:
            g[(x, ey + 6)] = ("o",)
            g[(x, ey + 7)] = ("o",)
    g[(ex + 4, ey + 4)] = ("bone", 0)
    g[(ex + 4, ey + 3)] = ("bone", 0)
    if P["mouth"]:
        g[(ex + 1, ey + 7)] = ("bone", 1)
    return g


# ============================================================================= THE HOLLOW
def greatsword(c, fist, ang, ln=26, w=2.5, ramp="iron"):
    tip = polar(fist, ang, ln)
    u = (math.cos(math.radians(ang)), math.sin(math.radians(ang)))
    n = (-u[1], u[0])
    b0 = (fist[0] + u[0] * 3, fist[1] + u[1] * 3)
    c.poly([(b0[0] + n[0] * w, b0[1] + n[1] * w), (tip[0] + n[0] * w * 0.6, tip[1] + n[1] * w * 0.6),
            (tip[0] + u[0] * 3, tip[1] + u[1] * 3),
            (tip[0] - n[0] * w * 0.8, tip[1] - n[1] * w * 0.8), (b0[0] - n[0] * w, b0[1] - n[1] * w)], ramp)
    for t in (0.35, 0.65):
        p = lerp(b0, tip, t)
        q = (int(p[0] - n[0] * (w - 0.3)), int(p[1] - n[1] * (w - 0.3)))
        c.t.pop(q, None)
        c.part.pop(q, None)
    c.stick((fist[0] - n[0] * 2 * w, fist[1] - n[1] * 2 * w), (fist[0] + n[0] * 2 * w, fist[1] + n[1] * 2 * w), 2.6, 2.6, "plate")
    c.stick(fist, (fist[0] - u[0] * 4, fist[1] - u[1] * 4), 2.6, 2.6, "leath")
    return b0, tip


def smoke_wisps(c, x, y, f, n=3, size=1.0):
    for i in range(n):
        k = (f + i) % 4
        c.blob(x - i * 2 * size + k * 0.5, y - (k * 2.2 + i) * size, (2.2 - k * 0.4) * size, (1.8 - k * 0.3) * size, "smoke")


def hollow_knight(c, P):  # grunt, 64x72: plate-armoured shadow brute with a notched greatsword
    G = 71
    lean = P["lean"] + P["shake"]
    by = P["bob"] + P["crouch"]
    hip = (28 + lean, 41 + by)
    lag = (0, 1, 0, -1)[P["f"] % 4] if P["anim"] == "walk" else 1
    C = [(24, 18), (33, 17), (30, 38), (26, 52), (22, 49), (19, 56), (15, 51), (10, 57), (9, 44), (16, 28)]
    c.poly([(x + lean - (lag if y > 40 else 0), y + by) for x, y in C], "cloak")
    ff = foot(P, "far", 28, G, 6, 3)
    fk = ik(hip, ff, 15, 15)
    c.stick(hip, fk, 9, 7, "plate", dark=1)
    c.stick(fk, ff, 7, 6, "plate", dark=1)
    boot(c, ff, 9, "plate", dark=1, ht=3)
    c.stick((26 + lean, 22 + by), (23 + lean - P["sway"] * 2.4, 37 + by), 6, 5, "plate", dark=1)
    c.poly([(x + lean, y + by) for x, y in ((21, 40), (35, 40), (38, 47), (30, 49), (20, 46))], "plate")
    c.poly([(x + lean, y + by) for x, y in ((23, 41), (35, 41), (37, 33), (40, 24), (34, 18), (24, 19), (20, 27))], "plate")
    for x, y in ((30, 26), (31, 27), (31, 28), (32, 29), (30, 30)):
        c.px(x + lean, y + by, "eye", 1)
    nf = foot(P, "near", 30, G, 6, 3)
    nk = ik(hip, nf, 15, 15)
    c.stick(hip, nk, 10, 8, "plate")
    c.blob(nk[0] + 1, nk[1], 4, 3.4, "iron")
    c.stick(nk, nf, 8, 6.5, "plate")
    boot(c, nf, 10, "plate", ht=4)
    hx, hy = 32 + lean * 1.4, 11 + by + P["tilt"]
    c.stick((hx - 3, hy - 3), (hx - 10, hy - 8), 4, 3, "bone")
    c.stick((hx - 10, hy - 8), (hx - 17, hy - 9), 3, 1.5, "bone")
    c.poly([(hx - 6, hy - 4), (hx + 2, hy - 6), (hx + 6, hy - 1), (hx + 6, hy + 7), (hx - 1, hy + 9), (hx - 6, hy + 5)], "plate")
    for dx in (-4, -1, 2):
        c.poly([(hx + dx - 1.5, hy - 4), (hx + dx + 1.5, hy - 5), (hx + dx, hy - 9)], "plate")
    px_, py_ = 33 + lean, 21 + by
    c.blob(px_, py_, 6.5, 4.5, "plate")
    c.poly([(px_ - 6, py_ + 2), (px_ + 6.5, py_ + 1), (px_ + 5, py_ + 5), (px_ - 5, py_ + 5)], "plate")
    c.poly([(px_ - 2, py_ - 3), (px_ + 1.5, py_ - 4), (px_ - 4, py_ - 10)], "iron")
    sh = (34 + lean, 24 + by)
    dx, dy, ang = keyed(P["swing"], [(6 - P["sway"] * 2, 14, 56), (-8 - lean, -12, 209), (10, 10, 430)])
    fist = (sh[0] + dx, sh[1] + dy)
    el = ik(sh, fist, 8, 8, bend=-1)
    greatsword(c, fist, ang)
    c.stick(sh, el, 7, 6, "plate")
    c.stick(el, fist, 6, 5, "plate")
    c.blob(el[0], el[1], 3, 2.8, "iron")
    c.blob(fist[0], fist[1], 3.2, 3, "plate")
    smoke_wisps(c, 26 + lean, 14 + by, P["f"])
    g = c.finish(P["warn"])
    ex, ey = int(round(hx + 1)), int(round(hy + 1))
    for x in range(ex - 3, ex + 6):
        g[(x, ey)] = ("o",)
    g[(ex + 2, ey)] = ("eye", 0)
    g[(ex + 3, ey)] = ("eye", 1)
    g[(ex + 4, ey)] = ("eye", 1)
    return g


def wraith_hound(c, P):  # skirmisher, 64x48: a gaunt shadow beast with a bone-skull face, lunging bite
    G = 47
    k = 2
    ox = P["lean"] * k + P["shake"]
    by = P["bob"] + P["crouch"] * 1.5
    sh, hp = (41 + ox, 24 + by), (20 + ox * 0.5, 23 + by)
    # far legs (darker): far front follows "far", far back follows "near"
    for base, which, bx, bend, l1, l2 in ((sh, "far", 42, -1, 10, 11), (hp, "near", 18, 1, 10, 12)):
        ft = foot(P, which, bx, G, 6, 3)
        kn = ik(base, ft, l1, l2, bend)
        c.stick(base, kn, 5, 3.5, "hide", dark=1)
        c.stick(kn, ft, 3.5, 2.5, "hide", dark=1)
        c.poly([(ft[0] - 1, ft[1] - 1.5), (ft[0] + 4, ft[1]), (ft[0] - 1, ft[1] + 1)], "hide", dark=1)
    wag = (0, -1, 0, 1)[P["f"] % 4]
    for i, (x, y) in enumerate(((14, 20), (9, 17), (4, 15))):                              # smoky tattered tail
        c.poly([(x + ox * 0.5 + 3, y + by), (x + ox * 0.5 - 5, y + by - 3 + wag * i), (x + ox * 0.5 - 4, y + by + 1 + wag * i),
                (x + ox * 0.5 + 1, y + by + 3)], "cloak")
    thorns(c, [(x + ox * (0.5 + i * 0.1), 18 + by - (i % 2)) for i, x in enumerate((19, 24, 29, 34))], size=1.1)
    body = [(15, 21), (22, 17), (35, 16), (45, 18), (46, 27), (38, 29), (29, 26), (21, 28), (15, 26)]
    c.poly([(x + ox * (0.5 + (x - 15) / 60), y + by) for x, y in body], "hide")
    for x in range(30, 39, 2):                                                           # ribs showing through
        for y in range(20, 26):
            if (y + x) % 5:
                c.px(x + ox * 0.9, y + by, "bone", 2)
    for x, ln in ((24, 4), (28, 5), (32, 4), (36, 5)):                                  # tattered belly
        xx = x + ox * 0.8
        c.poly([(xx - 2, 26.5 + by), (xx + 2, 26.5 + by), (xx + 0.5, 26.5 + by + ln)], "cloak")
    mane = [(33, 15), (42, 13), (48, 18), (46, 24), (43, 21), (41, 26), (38, 21), (35, 24), (31, 19)]
    c.poly([(x + ox, y + by) for x, y in mane], "cloak")
    for base, which, bx, bend, l1, l2 in ((sh, "near", 44, -1, 10, 11), (hp, "far", 21, 1, 10, 12)):
        ft = foot(P, which, bx, G, 6, 3)
        kn = ik(base, ft, l1, l2, bend)
        c.stick(base, kn, 5.5, 4, "hide")
        c.stick(kn, ft, 4, 3, "hide")
        c.poly([(ft[0] - 1, ft[1] - 2), (ft[0] + 4.5, ft[1]), (ft[0] - 1, ft[1] + 1)], "hide")
        c.px(ft[0] + 4, ft[1] + 0.5, "bone", 0)
    low = P["crouch"] * 1.5 if P["anim"] in ("windup", "strike") else 0
    hx, hy = 51 + ox * 1.2, 20 + by + P["tilt"] + low
    c.stick((sh[0] + 1, sh[1] - 3), (hx - 2, hy + 1), 8, 6, "hide")
    c.poly([(hx - 4, hy - 3), (hx - 12, hy - 8), (hx - 7, hy - 1)], "hide")              # torn ear
    jaw = 28 if P["mouth"] else 4
    J = rot([(-3, 3), (9, 3.5), (8.5, 5.5), (-2, 6)], (hx - 3, hy + 3), jaw)
    c.poly(J, "bone", dark=1)
    c.poly([(hx - 5, hy - 3.5), (hx + 3, hy - 4), (hx + 11, hy + 1), (hx + 10.5, hy + 3.5), (hx - 1, hy + 3.5), (hx - 5, hy + 1.5)], "bone")
    g = c.finish(P["warn"])
    for t in (0.3, 0.55, 0.8):                                                           # teeth
        p = lerp((hx, hy + 3.5), (hx + 10, hy + 3.5), t)
        g[(int(round(p[0])), int(round(p[1])))] = ("bone", 0)
        q = lerp(J[0], J[1], t)
        g[(int(round(q[0])), int(round(q[1])) - 1)] = ("bone", 0)
    ex, ey = int(round(hx + 1)), int(round(hy - 1))
    g[(ex - 1, ey)] = ("o",)
    g[(ex, ey)] = ("eye", 0)
    g[(ex + 1, ey)] = ("eye", 1)
    g[(ex + 2, ey)] = ("o",)
    g[(ex, ey - 1)] = ("o",)
    g[(ex + 1, ey - 1)] = ("o",)
    return g


def hollow_colossus(c, P):  # brute, 80x80: a hulking armoured giant with iron fists, double-fist smash
    G = 79
    k = 1.6
    ox, by = P["lean"] * k + P["shake"], (P["bob"] + P["crouch"]) * k
    hip = (35 + ox, 54 + by)
    ff = foot(P, "far", 32, G, 6, 3)
    fk = ik(hip, ff, 12, 13)
    c.stick(hip, fk, 13, 11, "plate", dark=1)
    c.stick(fk, ff, 11, 10, "plate", dark=1)
    boot(c, ff, 14, "plate", dark=1, ht=5)
    sh2 = (36 + ox, 27 + by)
    dx, dy, _ = keyed(P["swing"], [(7 - P["sway"] * 3, 32, 0), (-6 - ox * 0.5, -21, 0), (19, 30, 0)])
    f2 = (sh2[0] + dx - 5, sh2[1] + dy + 1)
    e2 = ik(sh2, f2, 13, 13, bend=-1)
    c.stick(sh2, e2, 11, 10, "plate", dark=1)
    c.stick(e2, f2, 10, 9, "plate", dark=1)
    c.blob(f2[0], f2[1], 6, 5.5, "iron", dark=1)
    c.blob(33 + ox, 25 + by, 10, 7, "plate", dark=1)
    c.poly([(x + ox, y + by) for x, y in ((21, 56), (49, 56), (55, 45), (57, 30), (49, 19), (32, 17), (21, 25), (17, 40))], "plate")
    for x, y in ((39, 32), (40, 33), (40, 34), (41, 35), (39, 37), (38, 38), (42, 36)):  # glowing cracks
        c.px(x + ox, y + by, "eye", 1)
    for x, y in ((26, 22), (32, 19)):                                                   # smoke vents on the back
        smoke_wisps(c, x + ox, y + by, P["f"] + x, n=2, size=1.4)
    mt = [(19, 31), (24, 21), (33, 16), (46, 17), (51, 22), (46, 26), (42, 23), (39, 30), (35, 25), (31, 33), (27, 27), (23, 36)]
    c.poly([(x + ox, y + by) for x, y in mt], "cloak")                                    # tattered mantle over the hump
    lc = [(28, 53), (44, 53), (43, 68), (40, 64), (37, 70), (34, 64), (31, 69)]
    c.poly([(x + ox * 0.8, y + by) for x, y in lc], "cloak")
    nf = foot(P, "near", 40, G, 6, 3)
    nk = ik(hip, nf, 12, 13)
    c.stick(hip, nk, 14, 12, "plate")
    c.blob(nk[0] + 2, nk[1], 6, 5, "iron")
    c.stick(nk, nf, 12, 11, "plate")
    boot(c, nf, 15, "plate", ht=5)
    sh = (47 + ox, 29 + by)
    c.blob(sh[0] - 2, sh[1] - 3, 8.5, 6.5, "plate")
    for i in range(3):
        c.poly([(sh[0] - 8 + i * 4, sh[1] - 8), (sh[0] - 5 + i * 4, sh[1] - 9), (sh[0] - 9 + i * 4, sh[1] - 16 + i)], "iron")
    hx, hy = 58 + ox * 1.2, 24 + by + P["tilt"]
    c.stick((hx - 7, hy + 3), (hx - 1, hy + 1), 7, 7, "plate")
    for s in (-1, 1):
        c.stick((hx - 1, hy - 3 + s), (hx + 6, hy - 9 + s * 2), 3.5, 2, "bone", dark=(1 if s > 0 else 0))
    c.poly([(hx - 5, hy - 5), (hx + 3, hy - 6), (hx + 7, hy - 1), (hx + 7, hy + 5), (hx - 4, hy + 6)], "plate")
    fist = (sh[0] + dx, sh[1] + dy)
    el = ik(sh, fist, 14, 14, bend=-1)
    c.stick(sh, el, 12, 11, "plate")
    c.blob(el[0], el[1], 5, 4.5, "iron")
    c.stick(el, fist, 11, 10, "plate")
    c.blob(fist[0], fist[1], 8, 7.5, "iron")
    g = c.finish(P["warn"])
    ex, ey = int(round(hx + 2)), int(round(hy))
    for x in range(ex - 3, ex + 5):
        g[(x, ey)] = ("o",)
    g[(ex + 2, ey)] = ("eye", 0)
    g[(ex + 3, ey)] = ("eye", 1)
    return g


KING_SPECIAL = [dict(swing=.8, lean=-1, crouch=1),
                dict(swing=1, lean=-2, crouch=-1, tilt=-1, warn=True),
                dict(plunge=1, lean=2, crouch=3),
                dict(plunge=1, lean=2, crouch=4, glow=1),
                dict(plunge=1, lean=2, crouch=4, glow=1, shake=1),
                dict(plunge=1, lean=1, crouch=3)]


def hollow_king(c, P):  # boss, 80x88: crowned, cloaked, ornate plate, a black greatsword, ground-plunge special
    G = 87
    k = 1.4
    ox, by = P["lean"] * k + P["shake"], (P["bob"] + P["crouch"]) * k
    hip = (38 + ox, 52 + by)
    lag = (0, 1, 0, -1)[P["f"] % 4] if P["anim"] == "walk" else 2
    cl = [(30, 22), (42, 20), (38, 50), (34, 70), (31, 86), (25, 82), (20, 86), (15, 81), (9, 86), (6, 76), (12, 56), (20, 34)]
    c.poly([(x + ox - (lag * (y - 40) / 40 if y > 40 else 0), y + by * (1 if y < 60 else 0.3)) for x, y in cl], "cloak")
    c.poly([(x + ox, y + by) for x, y in ((31, 22), (33, 9), (36, 17), (40, 20))], "cloak")    # high collar
    ff = foot(P, "far", 36, G, 7, 3)
    fk = ik(hip, ff, 17, 17)
    c.stick(hip, fk, 10, 8, "plate", dark=1)
    c.stick(fk, ff, 8, 7, "plate", dark=1)
    boot(c, ff, 11, "plate", dark=1, ht=4)
    c.poly([(x + ox, y + by) for x, y in ((29, 51), (47, 51), (50, 62), (44, 65), (38, 60), (31, 64), (27, 60))], "plate")
    c.poly([(x + ox, y + by) for x, y in ((30, 53), (46, 53), (49, 43), (52, 30), (45, 22), (33, 23), (28, 34))], "plate")
    for i in range(8):                                                                    # bone trim on the breastplate
        p = lerp((31, 31), (49, 30), i / 7)
        c.px(p[0] + ox, p[1] + by, "bone", 1)
    c.blob(40 + ox, 38 + by, 2.6, 2.6, "eye", flat=1)                                     # hollow heart-light
    for x, y in ((37, 41), (36, 43), (43, 36), (44, 34)):
        c.px(x + ox, y + by, "eye", 1)
    nf = foot(P, "near", 41, G, 7, 3)
    nk = ik(hip, nf, 17, 17)
    c.stick(hip, nk, 11, 9, "plate")
    c.blob(nk[0] + 1, nk[1], 4.5, 4, "iron")
    c.stick(nk, nf, 9, 7.5, "plate")
    boot(c, nf, 12, "plate", ht=4)
    hx, hy = 43 + ox * 1.2, 13 + by + P["tilt"]
    c.poly([(hx - 5, hy - 4), (hx + 3, hy - 5), (hx + 6, hy), (hx + 6, hy + 8), (hx, hy + 10), (hx - 5, hy + 6)], "plate")
    for dx, ht in ((-5, 6), (-2.5, 9), (0.5, 11), (3, 8), (5, 5)):                         # crown of iron spikes
        c.poly([(hx + dx - 1.3, hy - 3.5), (hx + dx + 1.3, hy - 4), (hx + dx, hy - 4 - ht)], "iron")
    c.poly([(hx - 6, hy - 4.5), (hx + 6, hy - 5), (hx + 6.5, hy - 2.5), (hx - 6, hy - 2)], "iron")
    smoke_wisps(c, hx - 6, hy - 6, P["f"], n=3, size=1.2)
    px_, py_ = 45 + ox, 24 + by
    c.blob(px_, py_, 7.5, 5, "plate")
    c.poly([(px_ - 7, py_ + 2), (px_ + 7.5, py_ + 1), (px_ + 6, py_ + 6), (px_ - 6, py_ + 6)], "plate")
    c.poly([(px_ - 6, py_ + 6), (px_ + 6, py_ + 5.5), (px_ + 5, py_ + 9), (px_ - 5, py_ + 9)], "plate")
    for i in range(6):
        p = lerp((px_ - 6, py_ + 1.5), (px_ + 6, py_ + 0.5), i / 5)
        c.px(p[0], p[1], "bone", 1)
    sh = (45 + ox, 27 + by)
    if P["plunge"]:
        fist = (sh[0] + 10, G - 30 - P["crouch"] * 0.3)
        ang = 90
    else:
        dx, dy, ang = keyed(P["swing"], [(7 - P["sway"] * 2, 17, 70), (-10 - ox * 0.5, -16, 200), (12, 14, 430)])
        fist = (sh[0] + dx, sh[1] + dy)
    c.stick((38 + ox, 27 + by), (fist[0] - 2, fist[1] + 1), 6, 5, "plate", dark=1)        # far arm on the hilt
    el = ik(sh, fist, 10, 10, bend=-1)
    b0, tip = greatsword(c, fist, ang, ln=34, w=3, ramp="plate")
    for t in (0.3, 0.45, 0.6):                                                          # runes along the fuller
        p = lerp(b0, tip, t)
        c.px(p[0], p[1], "eye", 1)
    c.stick(sh, el, 8, 7, "plate")
    c.blob(el[0], el[1], 3.5, 3.2, "iron")
    c.stick(el, fist, 7, 6, "plate")
    c.blob(fist[0], fist[1], 3.6, 3.4, "plate")
    g = c.finish(P["warn"])
    ex, ey = int(round(hx + 1)), int(round(hy + 2))
    for x in range(ex - 3, ex + 6):
        g[(x, ey)] = ("o",)
    g[(ex + 2, ey)] = ("eye", 0)
    g[(ex + 3, ey)] = ("eye", 1)
    g[(ex + 4, ey)] = ("eye", 1)
    if P["mouth"] or P["glow"]:
        g[(ex + 3, ey - 1)] = ("eye", 1)
        g[(ex + 3, ey + 1)] = ("eye", 1)
    return g


# ============================================================================= defeats
def hsh(x, y, s=0):
    v = (x * 73856093) ^ (y * 19349663) ^ (s * 83492791)
    return (v % 1000) / 1000


def defeat_leaves(base, w, h, zone):
    # Bursts into leaves (Gloomlings): the body breaks up, leaves fly out and flutter down.
    pts = [p for p, t in base.items() if t[0] not in ("o", "warn")]
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    seeds = [p for p in pts if hsh(*p) < max(0.05, 18 / len(pts))][:40]
    frames = [base]

    def leaves(g, dist, fall, keep=1.0):
        for i, (x, y) in enumerate(seeds):
            if hsh(x, y, 7) > keep:
                continue
            dx, dy = x - cx, y - cy
            ln = math.hypot(dx, dy) or 1
            lx = int(round(x + dx / ln * dist * (0.7 + hsh(x, y, 3))))
            ly = int(round(y + dy / ln * dist * 0.6 - dist * 0.4 + fall))
            shape_a = (((0, 0), (zone, 0)), ((1, 0), (zone, 1)), ((1, 1), (zone, 2)), ((0, 1), ("o",)))
            shape_b = (((0, 0), (zone, 1)), ((0, 1), (zone, 2)), ((1, 1), (zone, 0)), ((1, 0), ("o",)))
            for (a, b), tok in (shape_a if i % 2 else shape_b):
                if 0 <= lx + a < w and 0 <= ly + b < h:
                    g[(lx + a, ly + b)] = tok
            if i % 5 == 0 and 0 <= lx - 1 < w and 0 <= ly < h:
                g[(lx - 1, ly)] = ("wood", 1)                                               # a twig bit
        return g

    frames.append(leaves({p: t for p, t in base.items() if hsh(*p, 1) < 0.45}, 3, 0))
    frames.append(leaves({}, 7, 0))
    frames.append(leaves({}, 10, 5, keep=0.55))
    return frames


def defeat_smoke(base, w, h):
    # Dissolves into black smoke (the Hollow): pixels turn to smoke, rise and thin out.
    frames = [base]
    for f, (gone, smoky, rise) in enumerate(((0.25, 0.6, 1), (0.6, 0.92, 3), (0.9, 1.0, 7)), 1):
        g = {}
        for (x, y), t in base.items():
            r = hsh(x, y, 11)
            if t[0] == "eye" and f < 3:
                g[(x, y - f)] = ("eye", 1)
                continue
            if r < gone:
                continue
            ny = y - int(rise * (0.5 + hsh(x, y, 5)))
            if r < smoky or f == 3:
                g[(x, ny)] = ("smoke", 1 if hsh(x, y, 9) < 0.5 else 2)
            else:
                g[(x, ny)] = t
        frames.append({p: t for p, t in g.items() if 0 <= p[1] < h})
    return frames


def defeat_flee(fn, w, h, weapon, rest, ground):
    # Drops its gear and flees (Thornbacks): stagger, the weapon falls, then it turns and runs.
    # The runner is mirrored to face away; root_dx (drawn space) slides it off, the dropped gear stays put.
    def gear(t, dxw):
        c = Canvas(w, h)
        (x0, y0, a0), (x1, y1, a1) = rest, ground
        weapon(c, (x0 + (x1 - x0) * t + dxw, y0 + (y1 - y0) * t * t), a0 + (a1 - a0) * t)
        return c.finish()

    frames, roots = [fn(Canvas(w, h), pose("defeat", 0))], [0, 0, -3, -8]
    P1 = pose("defeat", 0)
    P1.update(gear="none", lean=-2, crouch=1, mouth=1)
    g = gear(0.5, 0)
    g.update(fn(Canvas(w, h), P1))
    frames.append(g)
    for f, wf in ((2, 1), (3, 3)):
        P2 = pose("walk", wf)
        P2.update(gear="none", lean=2, mouth=1)
        body = fn(Canvas(w, h), P2)
        g = gear(1, -roots[f])
        g.update({(w - 1 - x, y): t for (x, y), t in body.items()})
        frames.append(g)
    return frames, roots


# ============================================================================= boss effects
def fx_spores(f, w, h):
    # Gloom Mother: spores gather at the staff, then burst out along the ground in front of her.
    g = {}
    if f == 2:
        for i in range(6):
            a = i * 60 + 20
            p = polar((22, 4), a, 4)
            g[(int(p[0]), int(p[1]))] = ("spore", 0)
    if f >= 3:
        r = (f - 2) * 9
        for i in range(30):
            a = -170 + i * 12 + hsh(i, f) * 8
            d = r * (0.5 + hsh(i, 3, f) * 0.6)
            cx, cy = 48 + d * math.cos(math.radians(a)) * 1.6, 46 + d * math.sin(math.radians(a)) * 0.7
            if cy > 50:
                continue
            rad = 1.8 + (f - 3) * 0.6 - (0.8 if f == 5 and i % 2 else 0)
            for y in range(int(cy - rad), int(cy + rad) + 1):
                for x in range(int(cx - rad), int(cx + rad) + 1):
                    dd = math.hypot(x - cx, y - cy)
                    if dd <= rad and 0 <= x < w and 0 <= y < h:
                        g[(x, y)] = ("spore", 0 if dd < rad * 0.4 else 1 if dd < rad * 0.75 else 2 + (f == 5))
    return g


def fx_shock(f, w, h):
    # Thornback Chief: dust and rock chunks thrown up where the cleaver hits the ground.
    g = {}
    if f < 3:
        return g
    G, x0 = 63, 52
    s = f - 2
    for side in (-1, 1):
        for i in range(5):
            cx = x0 + side * (4 + i * 4) * s * 0.7
            cy = G - 2 - (5 - i) * 0.8 * (1 if f < 5 else 0.6)
            rad = (3.2 - i * 0.4) * (0.8 + s * 0.25)
            for y in range(int(cy - rad), int(cy + rad) + 1):
                for x in range(int(cx - rad * 1.3), int(cx + rad * 1.3) + 1):
                    dd = math.hypot((x - cx) / 1.3, y - cy)
                    if dd <= rad and 0 <= x < w and 0 <= y <= G:
                        g[(x, y)] = ("dust", 0 if (dd < rad * 0.5 and y < cy) else 1 if dd < rad * 0.8 else 2 + (f == 5))
    for i in range(7):
        a = -150 + i * 20
        p = polar((x0, G - 2), a, 6 + s * 6 + hsh(i, 1) * 4)
        p = (p[0], p[1] + s * s * 0.8)
        for dx, dy in ((0, 0), (1, 0), (0, 1)):
            x, y = int(p[0]) + dx, int(p[1]) + dy
            if 0 <= x < w and 0 <= y <= G:
                g[(x, y)] = ("rock", 1 if dx + dy else 0)
    return g


def fx_spikes(f, w, h):
    # Hollow King: spectral spikes and black smoke erupt along the ground from the plunged sword.
    g = {}
    G, x0 = 87, 60
    if f == 2 or f == 3:
        for i in range(10):
            g[(x0 + i * (f - 1) * 2, G - 1)] = ("spore", 1)
    if f >= 3:
        for i in range(6):
            x = x0 + 6 + i * 10
            age = f - 3 - i * 0.5
            if age < -0.5 or (f == 5 and i < 2):
                continue
            ht = max(3, 16 - i * 1.5) * min(1, age + 1)
            for y in range(int(G - ht), G):
                half = 2.5 * (y - (G - ht)) / ht + 0.3
                for xx in range(int(x - half), int(x + half) + 1):
                    if 0 <= xx < w:
                        g[(xx, y)] = ("spore", 0 if xx <= x - half + 1 else 1 if xx < x + 0.5 else 2)
            for k in range(3):
                cx, cy = x - 3 + k * 3, G - 2 - k
                for yy in range(cy - 2, cy + 2):
                    for xx in range(cx - 2, cx + 2):
                        if (xx, yy) not in g and 0 <= xx < w and hsh(xx, yy, f) < 0.7:
                            g[(xx, yy)] = ("smoke", 1)
    return g


# ============================================================================= assembly
ENEMIES = {  # name: (w, h, element-zone ramp, builder, defeat style, boss special)
    "twig_imp":        (24, 24, "moss", twig_imp, "leaves", None),
    "leaf_darter":     (24, 24, "moss", leaf_darter, "leaves", None),
    "mossy_lump":      (32, 28, "moss", mossy_lump, "leaves", None),
    "gloom_mother":    (56, 52, "moss", gloom_mother, "leaves", (MOTHER_SPECIAL, fx_spores, 96)),
    "club_thug":       (40, 40, "skin", club_thug, ("flee", club, (31, 31, 55), (28, 37, 180)), None),
    "sling_runner":    (36, 40, "skin", sling_runner, ("flee", sling, (20, 24, 100), (24, 38, 180)), None),
    "shield_brute":    (48, 44, "skin", shield_brute, ("flee", lambda c, p, a: shield(c, p, a), (33, 26, 0), (24, 39, 90)), None),
    "thornback_chief": (56, 64, "skin", thornback_chief, ("flee", cleaver, (38, 37, 60), (36, 60, 185)), (CHIEF_SPECIAL, fx_shock, 112)),
    "hollow_knight":   (64, 72, "cloak", hollow_knight, "smoke", None),
    "wraith_hound":    (64, 48, "cloak", wraith_hound, "smoke", None),
    "hollow_colossus": (80, 80, "cloak", hollow_colossus, "smoke", None),
    "hollow_king":     (80, 88, "cloak", hollow_king, "smoke", (KING_SPECIAL, fx_spikes, 160)),
}
BASE = {"walk": 4, "windup": 2, "strike": 3, "hit": 2, "defeat": 4}


def colour(tok):
    if tok[0] == "o":
        return OUTLINE
    if tok[0] == "warn":
        return WARN
    return R[tok[0]][tok[1]]


def write(path, w, h, zone, anims, attach=None, extra=None):
    pal, inv = {}, {}
    if zone:
        for i, s in enumerate("1234"):
            pal[s] = R[zone][i]
            inv[(zone, i)] = s
    pal["e"], pal["E"] = R["eye"][0], R["eye"][1]
    inv[("eye", 0)] = "e"
    for i in (1, 2, 3):
        inv[("eye", i)] = "E"
    pal["o"], inv[("o",)] = OUTLINE, "o"
    pal["r"], inv[("warn",)] = WARN, "r"
    spare = iter(c for c in "abcdfghijklmnpqstuvwxyzABCDFGHIJKLMNPQRSTUVWXYZ056789" if c not in pal)
    by_colour = {}
    for frames in anims.values():
        for fr in frames:
            for tok in fr.values():
                if tok in inv:
                    continue
                col = colour(tok)
                key = col + "x" if (zone and col in R[zone]) or col in R["eye"] else col
                if key not in by_colour:
                    by_colour[key] = next(spare)
                    pal[by_colour[key]] = col
                inv[tok] = by_colour[key]
    grids = {a: [["".join(inv[fr[(x, y)]] if (x, y) in fr else "." for x in range(w)) for y in range(h)]
                 for fr in frames] for a, frames in anims.items()}
    d = {"width": w, "height": h, "fps": 8, "palette": pal,
         "dye_zones": ({"element": "1234"} if zone else {}) | {"eyes": "eE"},
         "attach": attach or {}, "animations": grids}
    if zone:
        d["element_ramps"] = ELEMENT_RAMPS
    d.update(extra or {})
    json.dump(d, open(path, "w"))


def flash(g):
    return {p: (t if t[0] in ("o", "warn", "eye") else (t[0], 0)) for p, t in g.items()}


def build(name):
    w, h, zone, fn, dstyle, boss = ENEMIES[name]
    anims, attach = {}, {}
    for a, n in BASE.items():
        if a == "defeat":
            if dstyle == "leaves":
                anims[a] = defeat_leaves(fn(Canvas(w, h), pose(a, 0)), w, h, zone)
            elif dstyle == "smoke":
                anims[a] = defeat_smoke(fn(Canvas(w, h), pose(a, 0)), w, h)
            else:
                _, weapon, rest, ground = dstyle
                anims[a], roots = defeat_flee(fn, w, h, weapon, rest, ground)
                attach[a] = [{"root_dx": r} for r in roots]
            continue
        frames = []
        for f in range(n):
            P = pose(a, f)
            c = Canvas(w, h)
            g = fn(c, P)
            frames.append(flash(g) if P["flash"] else g)
            if name == "sling_runner" and a == "strike":
                attach.setdefault(a, []).append({"release": [round(c.release[0]), round(c.release[1])]} if f == 1 else {})
        anims[a] = frames
    if boss:
        seq, fx, fw = boss
        anims["roar"] = [fn(Canvas(w, h), pose("roar", f)) for f in range(4)]
        anims["special"] = [fn(Canvas(w, h), pose("special", f, seq)) for f in range(6)]
        write(f"{OUT}/{name}_special_fx.json", fw, h, None, {"special": [fx(f, fw, h) for f in range(6)]},
              extra={"anchor": [0, 0]})
    write(f"{OUT}/{name}.json", w, h, zone, anims, attach)
    print("wrote", name)


def sling_stone():
    frames = []
    for f in range(2):
        c = Canvas(6, 6)
        c.poly(rot([(-2, -1.5), (1.5, -2), (2.2, 1), (-1, 2)], (3, 3), f * 45), "rock")
        frames.append(c.finish())
    write(f"{OUT}/sling_stone.json", 6, 6, None, {"fly": frames})
    print("wrote sling_stone")


if __name__ == "__main__":
    names = [a for a in sys.argv[1:] if not a.startswith("-")] or list(ENEMIES)
    for nm in names:
        build(nm)
    if "sling_runner" in names:
        sling_stone()
