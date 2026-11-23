# Builds the enemies (ART_BRIEF §7): Gloomlings, Thornback bandits and the Hollow.
# Usage: python tools/build_enemies.py [--look]
#        then render each art/source/enemies/<enemy>.json with tools/render.py
#
# Enemies face right like everything else (the game flips them to face Skerbie).
# Same house style as Skerbie: flat faceted shading lit from the top-left, dark outline.
# Eyes are sickly yellow-green. Red is used only for the attack-warning flash: on the
# last windup frame the whole outline turns red.
#
# Elemental variants are palette swaps. Each enemy has one "element zone" drawn with the
# reserved characters 1 2 3 4 (highlight -> deep); the JSON lists the 4-shade ramp for
# ice, fire, water and lightning under "element_ramps". The game swaps them in and adds
# the matching elemental aura effect.
import json, math, os, sys

OUT = "art/source/enemies"
os.makedirs(OUT, exist_ok=True)
LOOK = "--look" in sys.argv
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
    "smoke": ["#33303d", "#23212b", "#17151c", "#17151c"],
    "eye":   ["#e4f27a", "#c8e04a", "#c8e04a", "#c8e04a"],
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
        # A deep seam where a later part sits on an earlier one of another material, then the outline.
        g = dict(self.t)
        for p, k in self.part.items():
            for dx, dy in N4:
                q = (p[0] + dx, p[1] + dy)
                if q in self.part and self.part[q] < k and self.t[q][0] != self.t[p][0] and self.t[p][0] != "eye":
                    g[p] = (self.t[p][0], 3)
                    break
        edge = {p for p in self.t if any((p[0] + dx, p[1] + dy) not in self.t for dx, dy in N4)}
        for (x, y), tok in self.t.items():
            # rim light: a pixel just inside the outline on the lit (top or left) side steps up a shade
            if (x, y) not in edge and tok[0] != "eye" and ((x, y - 1) in edge or (x - 1, y) in edge):
                g[(x, y)] = (tok[0], max(0, g[(x, y)][1] - 1))
        for p in edge:
            g[p] = ("warn",) if warn else ("o",)
        return g


def ik(hip, foot, l1, l2, bend=1):
    # Knee position for a two-bone leg; bend=+1 puts the knee forward (right).
    dx, dy = foot[0] - hip[0], foot[1] - hip[1]
    d = max(0.01, min(math.hypot(dx, dy), l1 + l2 - 0.01))
    a = math.acos(max(-1, min(1, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))))
    base = math.atan2(dy, dx)
    ang = base - a * bend
    return (hip[0] + l1 * math.cos(ang), hip[1] + l1 * math.sin(ang))


def walk_phase(f, stride, lift):
    # 4-frame walk: f0 near foot forward, f2 near foot back, swings lifted on f3 (near) / f1 (far).
    p = f / 4 * 2 * math.pi
    near = (stride * math.cos(p), -lift if f == 3 else 0)
    far = (-stride * math.cos(p), -lift if f == 1 else 0)
    bob = 0 if f % 2 == 0 else -1
    return near, far, bob


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


# ======================================================================= Gloomling: twig imp (24x24)
def twig_imp(c, anim, f):
    G = 23
    if anim == "walk":
        near, far, bob = walk_phase(f, 3, 2)
        lean, arm, crouch, raise_ = 0, near[0], 0, 0
    else:  # windup: crouch, lean back, near claw raised behind the head
        near, far, bob = (2, 0), (-2, 0), 0
        lean, crouch, arm = (-1, -2)[f], (1, 2)[f], 0
        raise_ = (0.8, 1.0)[f]
    hip = (11 + lean, 15 + bob + crouch)
    sh = (12 + lean * 1.5, 10 + bob + crouch)
    head = (13 + lean * 2, 6 + bob + crouch)
    # far limbs first (darker)
    fk = ik(hip, (11 + far[0], G - 1 + far[1]), 4, 4.5)
    c.stick(hip, fk, 3, 3, "wood", dark=1)
    c.stick(fk, (11 + far[0], G - 1 + far[1]), 3, 3, "wood", dark=1)
    c.stick((sh[0] - 1, sh[1] + 1), (sh[0] - 2 - arm * 0.6, sh[1] + 6), 3, 2.6, "wood", dark=1)
    # torso: a bundle of twigs bound with moss
    c.poly([(hip[0] - 2.5, hip[1] + 1), (hip[0] + 2.5, hip[1] + 1), (sh[0] + 2.5, sh[1]), (sh[0] - 2.5, sh[1] - 0.5)], "wood")
    c.blob(hip[0], hip[1] - 1, 3, 1.6, "moss")
    # near leg
    nf = (11 + near[0], G - 1 + near[1])
    nk = ik(hip, nf, 4, 4.5)
    c.stick(hip, nk, 3, 3, "wood")
    c.stick(nk, nf, 3, 3, "wood")
    c.poly([(nf[0] - 1, nf[1] - 1), (nf[0] + 2.5, nf[1] + 0.5), (nf[0] - 1, nf[1] + 1.2)], "wood")
    # head: a lumpy moss ball with a leafy crest, twig horns and a pointed twig snout
    hx, hy = head
    c.stick((hx - 3, hy - 2), (hx - 7, hy - 5), 2.6, 1.6, "wood")
    c.stick((hx - 1, hy - 3), (hx - 4, hy - 6.5), 2.6, 1.6, "wood")
    c.blob(hx, hy + 0.5, 6, 5, "moss")
    for i, (dx, ht) in enumerate(((-4.5, 2.5), (-1.5, 3.5), (1.5, 2.5))):
        c.poly([(hx + dx - 1.8, hy - 3.5), (hx + dx + 1.8, hy - 4), (hx + dx - 0.5, hy - 3.5 - ht)], "moss")
    c.poly([(hx + 4.5, hy - 0.5), (hx + 9.5, hy + 1.5), (hx + 4.5, hy + 3)], "wood")
    # near arm: a twig with claw tips; in the windup it is cocked back over the head
    if raise_:
        hand = lerp((sh[0] + 3, sh[1] + 5), (sh[0] - 4, sh[1] - 7), raise_)
    else:
        hand = (sh[0] + 1 - arm * 0.7, sh[1] + 6)
    c.stick(sh, hand, 3, 2.6, "wood")
    c.blob(sh[0], sh[1], 2, 1.6, "moss")
    out = (1 if not raise_ else -1)
    c.stick(hand, (hand[0] + 2 * out, hand[1] + (1 if not raise_ else -2)), 1.8, 1.2, "bone")
    g = c.finish(warn=(anim == "windup" and f == 1))
    # face, painted over the outline pass: big sickly eye and a toothy grin
    ex, ey = int(round(hx + 1)), int(round(hy - 1))
    for (x, y), s in (((ex, ey), 0), ((ex + 1, ey), 1), ((ex, ey + 1), 1), ((ex + 1, ey + 1), 1)):
        g[(x, y)] = ("eye", s)
    for x in range(ex, ex + 4):
        g[(x, ey + 3)] = ("o",)
    g[(ex + 1, ey + 2)] = ("bone", 0)
    return g


# ======================================================================= Thornback: club thug (40x40)
def club_thug(c, anim, f):
    G = 39
    if anim == "walk":
        near, far, bob = walk_phase(f, 4, 2)
        lean, crouch, sw = 0, 0, near[0] / 4
        fist, club = None, None
    else:
        near, far, bob = (3, 0), (-3, 0), 0
        lean, crouch, sw = (-1, -2)[f], (1, 2)[f], 0
    hip = (17 + lean, 28 + bob + crouch)
    # far leg and far arm
    ff = (17 + far[0], G - 1 + far[1])
    fk = ik(hip, ff, 6, 6)
    c.stick(hip, fk, 5, 4.5, "skin", dark=1)
    c.stick(fk, ff, 4.5, 4, "leath", dark=1)
    c.poly([(ff[0] - 2, ff[1] - 2), (ff[0] + 3.5, ff[1] - 0.5), (ff[0] + 3.5, ff[1] + 1), (ff[0] - 2, ff[1] + 1)], "leath", dark=1)
    by = bob + crouch
    c.stick((20 + lean, 18 + by), (17 + lean - sw, 27 + by), 4, 3.5, "skin", dark=1)
    # back thorns
    for i, (x, y) in enumerate(((13, 25), (12, 21), (13, 17), (16, 14))):
        x, y = x + lean, y + by
        c.poly([(x + 1, y - 2), (x + 3, y + 2), (x - 3.5 - i * 0.3, y - 2.5 - i * 0.6)], "bone")
    # torso: hunched back, pot belly
    T = [(12, 29), (23, 30), (27, 25), (26, 18), (20, 14), (14, 16), (11, 22)]
    c.poly([(x + lean, y + by) for x, y in T], "skin")
    # scrap chest plate, riveted, and a rope belt
    c.poly([(x + lean, y + by) for x, y in ((19, 18), (26, 19), (27.5, 25), (24, 28), (18, 26))], "iron")
    for x, y in ((21, 20), (25, 21), (24, 26)):
        c.px(x + lean, y + by, "iron", 0)
    c.poly([(x + lean, y + by) for x, y in ((12, 27), (24, 28), (23.5, 30.5), (12, 30))], "leath")
    # near leg
    nf = (19 + near[0], G - 1 + near[1])
    nk = ik(hip, nf, 6, 6)
    c.stick(hip, nk, 6, 5, "skin")
    c.stick(nk, nf, 5, 4.5, "leath")
    c.poly([(nf[0] - 2.5, nf[1] - 2), (nf[0] + 4, nf[1] - 0.5), (nf[0] + 4, nf[1] + 1), (nf[0] - 2.5, nf[1] + 1)], "leath")
    # head: dented pot helmet, big swept ear, hooked nose, underbite with a tusk
    hx, hy = 27 + lean * 1.5, 12 + by
    c.poly([(hx - 4, hy - 2), (hx - 13, hy - 7), (hx - 5, hy + 2)], "skin")
    c.blob(hx, hy, 5, 4.6, "skin")
    c.poly([(hx + 2.5, hy - 1.5), (hx + 9, hy + 2), (hx + 6, hy + 3.2), (hx + 3, hy + 2.5)], "skin")
    c.poly([(hx - 4, hy + 1.5), (hx + 4.5, hy + 2.5), (hx + 4, hy + 6), (hx - 3, hy + 5.5)], "skin")
    c.poly([(hx - 6, hy - 1), (hx - 5.5, hy - 4.5), (hx - 2, hy - 7), (hx + 2, hy - 7), (hx + 5, hy - 4), (hx + 5.5, hy - 1)], "iron")
    c.poly([(hx - 7, hy - 2), (hx + 6.5, hy - 2), (hx + 6.5, hy), (hx - 7, hy)], "rust")   # rusty brim band
    c.px(hx - 1, hy - 5, "iron", 3)                                                    # a dent
    c.px(hx + 1, hy - 1, "iron", 0)                                                    # a rivet
    # near arm and club
    if anim == "walk":
        sh = (21 + lean, 19 + by)
        fist = (25 + sw * 2, 27 + by)
        tip = (fist[0] + 6 + sw, fist[1] + 9)
    else:
        sh = (21 + lean, 19 + by)
        fist = lerp((24, 22 + by), (18 + lean, 8 + by), (0.75, 1.0)[f])
        tip = (fist[0] - 9, fist[1] - (5, 7)[f])
    el = ik(sh, fist, 5, 5.5, bend=-1)
    c.stick(fist, tip, 3, 5.5, "wood")
    for t in (0.6, 0.85):
        p = lerp(fist, tip, t)
        c.px(p[0] + 2, p[1] - 1, "bone", 0)
        c.px(p[0] - 2, p[1] + 1, "bone", 1)
    c.stick(sh, el, 5, 4.5, "skin")
    c.stick(el, fist, 4.5, 4, "skin")
    c.blob(fist[0], fist[1], 2.4, 2.2, "leath")
    g = c.finish(warn=(anim == "windup" and f == 1))
    ex, ey = int(round(hx + 1)), int(round(hy - 1))
    g[(ex, ey)] = ("eye", 0)
    g[(ex + 1, ey)] = ("eye", 1)
    for x in range(ex - 1, ex + 3):
        g[(x, ey - 1)] = ("o",)          # heavy brow
    for x in range(ex - 1, ex + 4):
        g[(x, ey + 4)] = ("o",)          # mouth line
    g[(ex + 3, ey + 3)] = ("bone", 0)    # tusk
    return g


# ======================================================================= Hollow: hollow knight (64x72)
def hollow_knight(c, anim, f):
    G = 71
    if anim == "walk":
        near, far, bob = walk_phase(f, 6, 3)
        lean, crouch = 0, 0
    else:
        near, far, bob = (5, 0), (-6, 0), 0
        lean, crouch = (-1, -3)[f], (1, 2)[f]
    by = bob + crouch
    hip = (28 + lean, 41 + by)
    # tattered cloak behind (element zone), drifting a frame behind the body
    lag = (0, 1, 0, -1)[f] if anim == "walk" else (1, 2)[f]
    C = [(24, 18), (33, 17), (30, 38), (26, 52), (22, 49), (19, 56), (15, 51), (10, 57), (9, 44), (16, 28)]
    c.poly([(x + lean - (lag if y > 40 else 0), y + by) for x, y in C], "cloak")
    # far leg
    ff = (28 + far[0], G - 1 + far[1])
    fk = ik(hip, ff, 15, 15)
    c.stick(hip, fk, 9, 7, "plate", dark=1)
    c.stick(fk, ff, 7, 6, "plate", dark=1)
    c.poly([(ff[0] - 3, ff[1] - 3), (ff[0] + 6, ff[1] - 1), (ff[0] + 6, ff[1] + 1), (ff[0] - 3, ff[1] + 1)], "plate", dark=1)
    # far arm
    c.stick((26 + lean, 22 + by), (23 + lean - near[0] * 0.4, 37 + by), 6, 5, "plate", dark=1)
    # torso and fauld plates
    c.poly([(x + lean, y + by) for x, y in ((21, 40), (35, 40), (38, 47), (30, 49), (20, 46))], "plate")
    c.poly([(x + lean, y + by) for x, y in ((23, 41), (35, 41), (37, 33), (40, 24), (34, 18), (24, 19), (20, 27))], "plate")
    # chest cracks leaking sickly light: the hollow inside
    for x, y in ((30, 26), (31, 27), (31, 28), (32, 29), (30, 30)):
        c.px(x + lean, y + by, "eye", 1)
    # near leg
    nf = (30 + near[0], G - 1 + near[1])
    nk = ik(hip, nf, 15, 15)
    c.stick(hip, nk, 10, 8, "plate")
    c.blob(nk[0] + 1, nk[1], 4, 3.4, "iron")           # knee cop
    c.stick(nk, nf, 8, 6.5, "plate")
    c.poly([(nf[0] - 3, nf[1] - 4), (nf[0] + 7, nf[1] - 1), (nf[0] + 7, nf[1] + 1), (nf[0] - 3, nf[1] + 1)], "plate")
    # great helm with a swept horn and a crown of spikes
    hx, hy = 32 + lean * 1.4, 11 + by
    c.stick((hx - 3, hy - 3), (hx - 10, hy - 8), 4, 3, "bone")
    c.stick((hx - 10, hy - 8), (hx - 17, hy - 9), 3, 1.5, "bone")
    c.poly([(hx - 6, hy - 4), (hx + 2, hy - 6), (hx + 6, hy - 1), (hx + 6, hy + 7), (hx - 1, hy + 9), (hx - 6, hy + 5)], "plate")
    for dx in (-4, -1, 2):
        c.poly([(hx + dx - 1.5, hy - 4), (hx + dx + 1.5, hy - 5), (hx + dx, hy - 9)], "plate")
    # near pauldron: layered plates with a spike
    px_, py_ = 33 + lean, 21 + by
    c.blob(px_, py_, 6.5, 4.5, "plate")
    c.poly([(px_ - 6, py_ + 2), (px_ + 6.5, py_ + 1), (px_ + 5, py_ + 5), (px_ - 5, py_ + 5)], "plate", dark=0)
    c.poly([(px_ - 2, py_ - 3), (px_ + 1.5, py_ - 4), (px_ - 4, py_ - 10)], "iron")
    # near arm and greatsword
    sh = (34 + lean, 24 + by)
    if anim == "walk":
        fist = (40 - near[0] * 0.3, 38 + by)
        tip = (fist[0] + 15, fist[1] + 22)
    else:
        fist = lerp((38, 30 + by), (26 + lean, 12 + by), (0.75, 1.0)[f])
        tip = (fist[0] - 22, fist[1] - (2, 0)[f] - 10)
    el = ik(sh, fist, 8, 8, bend=-1)
    # blade: a long notched slab, iron
    d = (tip[0] - fist[0], tip[1] - fist[1])
    ln = math.hypot(*d)
    u = (d[0] / ln, d[1] / ln)
    n = (-u[1], u[0])
    b0 = (fist[0] + u[0] * 3, fist[1] + u[1] * 3)
    c.poly([(b0[0] + n[0] * 2.5, b0[1] + n[1] * 2.5), (tip[0] + n[0] * 1.5, tip[1] + n[1] * 1.5),
            (tip[0] + u[0] * 3, tip[1] + u[1] * 3),
            (tip[0] - n[0] * 2, tip[1] - n[1] * 2), (b0[0] - n[0] * 2.5, b0[1] - n[1] * 2.5)], "iron")
    for t in (0.35, 0.65):                              # notches chipped out of the edge
        p = lerp(b0, tip, t)
        c.t.pop((int(p[0] - n[0] * 2.2), int(p[1] - n[1] * 2.2)), None)
    c.stick((fist[0] - n[0] * 5, fist[1] - n[1] * 5), (fist[0] + n[0] * 5, fist[1] + n[1] * 5), 2.6, 2.6, "plate")
    c.stick(fist, (fist[0] - u[0] * 4, fist[1] - u[1] * 4), 2.6, 2.6, "leath")
    c.stick(sh, el, 7, 6, "plate")
    c.stick(el, fist, 6, 5, "plate")
    c.blob(el[0], el[1], 3, 2.8, "iron")
    c.blob(fist[0], fist[1], 3.2, 3, "plate")
    # black smoke wisps rising off the shoulders
    for i in range(3):
        k = (f + i) % 4
        c.blob(26 + lean - i * 2 + k * 0.5, 14 + by - k * 2.2 - i, 2.2 - k * 0.4, 1.8 - k * 0.3, "smoke")
    g = c.finish(warn=(anim == "windup" and f == 1))
    # visor slit with one burning eye
    ex, ey = int(round(hx + 1)), int(round(hy + 1))
    for x in range(ex - 3, ex + 6):
        g[(x, ey)] = ("o",)
    g[(ex + 2, ey)] = ("eye", 0)
    g[(ex + 3, ey)] = ("eye", 1)
    g[(ex + 4, ey)] = ("eye", 1)
    return g


ENEMIES = {  # name: (w, h, element-zone ramp, builder, animations {name: frames})
    "twig_imp":      (24, 24, "moss", twig_imp),
    "club_thug":     (40, 40, "skin", club_thug),
    "hollow_knight": (64, 72, "cloak", hollow_knight),
}
ANIMS = {"walk": 4, "windup": 2}


def colour(tok):
    if tok[0] == "o":
        return OUTLINE
    if tok[0] == "warn":
        return WARN
    return R[tok[0]][tok[1]]


def to_json(name, w, h, zone, anims):
    pal, inv = {}, {}
    for i, s in enumerate("1234"):
        pal[s] = R[zone][i]
        inv[(zone, i)] = s
    pal["e"], pal["E"] = R["eye"][0], R["eye"][1]
    inv[("eye", 0)] = "e"
    for i in (1, 2, 3):
        inv[("eye", i)] = "E"
    pal["o"], inv[("o",)] = OUTLINE, "o"
    pal["r"], inv[("warn",)] = WARN, "r"
    spare = iter(c for c in "abcdfghijklmnpqstuvwxyzABCDFGHIJKLMNPQRSTUVWXYZ" if c not in pal)
    by_colour = {}
    for frames in anims.values():
        for fr in frames:
            for tok in fr.values():
                if tok in inv:
                    continue
                col = colour(tok)
                if col in R[zone] or col in R["eye"]:
                    col = col + "x"  # keep zone colours exclusive to the zone
                if col not in by_colour:
                    by_colour[col] = next(spare)
                    pal[by_colour[col]] = col.rstrip("x")
                inv[tok] = by_colour[col]
    grids = {a: [["".join(inv[fr[(x, y)]] if (x, y) in fr else "." for x in range(w)) for y in range(h)]
                 for fr in frames] for a, frames in anims.items()}
    json.dump({"width": w, "height": h, "fps": 8, "palette": pal,
               "dye_zones": {"element": "1234", "eyes": "eE"},
               "element_ramps": ELEMENT_RAMPS, "attach": {}, "animations": grids},
              open(f"{OUT}/{name}.json", "w"))


for name, (w, h, zone, fn) in ENEMIES.items():
    anims = {a: [fn(Canvas(w, h), a, f) for f in range(n)] for a, n in ANIMS.items()}
    to_json(name, w, h, zone, anims)
    print("wrote", name)
