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
import json, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_enemies import Canvas, R, ik, polar, lerp, rot  # noqa: E402

OUT = "art/source/tavern/beasts"
os.makedirs(OUT, exist_ok=True)
R.update({
    "boar":  ["#a8643a", "#7a5636", "#3b2a22", "#17151c"],
    "snout": ["#ffc8a8", "#f2a0b0", "#4a3a5c", "#2a2036"],
    "hoof":  ["#33303d", "#23212b", "#17151c", "#17151c"],
    "beye":  ["#ffd08a", "#ffb35c", "#ffb35c", "#ffb35c"],
    "tell":  ["#ffffff", "#fff4b0", "#fff4b0", "#fff4b0"],
})


def bpose(anim, f):
    P = dict(anim=anim, f=f, bob=0, lean=0, head=0, crouch=0, tell=False, sway=0, legs=(0, 0, 0, 0))
    if anim == "idle":
        P.update(bob=(0, -1, 0)[f], head=(0, -1, 1)[f], sway=(0, 1, 0)[f])
    elif anim == "tell":   # windup tell: drops its head, paws the floor, eyes flash on the last frame
        P.update([dict(lean=-1, head=1, crouch=1, legs=(0, 0, -2, 0)),
                  dict(lean=-2, head=2, crouch=2, legs=(0, -2, 0, 0)),
                  dict(lean=-2, head=3, crouch=2, tell=True, legs=(0, 0, -2, 0))][f])
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


def bramble_boar(c, P):  # 72x64: a hulking, hunched boar, bramble crest with glowing thorn tips, huge tusks
    G = 63
    ox, by = P["lean"], P["bob"] + P["crouch"]
    hy = P["head"] + 3                                                          # head held low: always ready to charge
    T = lambda pts: [(x + ox, y + by) for x, y in pts]
    # far legs (darker): front pair braced forward, hind pair pushing back
    for top, fx, which in (((41, 47), 45, 1), ((15, 47), 12, 3)):
        ft = (fx + P["legs"][which], G - 1)
        c.stick((top[0] + ox, top[1] + by), ft, 7, 5.5, "boar", dark=1)
        c.poly([(ft[0] - 3, ft[1] - 3), (ft[0] + 3.5, ft[1] - 3), (ft[0] + 3.5, ft[1] + 1), (ft[0] - 3, ft[1] + 1)], "hoof", dark=1)
    c.stick((10 + ox, 40 + by), (5 + ox, 37 + by - P["sway"]), 3, 2, "moss")             # vine tail
    c.stick((5 + ox, 37 + by - P["sway"]), (4 + ox, 42 + by), 2.4, 1.6, "moss")
    # body: a massive humped shoulder sloping down to a small rump
    c.poly(T([(8, 47), (10, 38), (18, 31), (30, 22), (40, 17), (48, 21), (53, 33), (51, 48), (38, 53), (20, 53), (11, 51)]), "boar")
    for x in range(14, 50, 3):
        c.px(x + ox, 52 + by + (x % 2), "boar", 3)
    for pts in (((22, 30), (26, 41), (22, 52)), ((35, 22), (38, 37), (34, 52))):        # vines round the flank
        pts = T(pts)
        c.stick(pts[0], pts[1], 2.2, 2.2, "moss", dark=1)
        c.stick(pts[1], pts[2], 2.2, 2.2, "moss", dark=1)
        c.blob(pts[1][0] + 2, pts[1][1] - 1, 2, 1.4, "moss")
    for top, fx, which in (((46, 47), 51, 0), ((19, 48), 17, 2)):                       # near legs
        ft = (fx + P["legs"][which], G - 1)
        c.stick((top[0] + ox, top[1] + by), ft, 8.5, 6.5, "boar")
        c.poly([(ft[0] - 3.5, ft[1] - 3), (ft[0] + 4, ft[1] - 3), (ft[0] + 4, ft[1] + 1), (ft[0] - 3.5, ft[1] + 1)], "hoof")
    # head: a long wedge driven low and forward, snout disc out front
    H_ = lambda pts: [(x + ox * 1.4, y + by + hy) for x, y in pts]
    c.poly(H_([(46, 24), (40, 15), (50, 22)]), "boar")                                   # ear, pinned back
    c.poly(H_([(43, 24), (51, 25), (57, 32), (62, 41), (62, 48), (56, 51), (49, 48), (44, 39)]), "boar")
    c.poly(H_([(48, 46), (57, 48), (56, 52), (49, 51)]), "boar", dark=1)                 # jaw
    c.poly(H_([(58, 39), (63.5, 40), (63.5, 50), (58.5, 50)]), "snout")
    # tusks: huge curved bone hooks from the jaw, sweeping forward and up past the snout
    for d, dk in ((-3, 1), (0, 0)):
        a, b, e, t = H_([(52 + d, 51), (61 + d, 51), (66 + d, 44), (64.5 + d, 35)])
        c.stick(a, b, 4.8, 4.2, "bone", dark=dk)
        c.stick(b, e, 4.2, 3.2, "bone", dark=dk)
        c.stick(e, t, 3.2, 1.2, "bone", dark=dk)
    # bristling bramble crest: thick thorny vines along the spine, long thorns raking back
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
    # an angry slanted brow over a burning eye (white-hot on the tell frame), nostrils
    ex, ey = c.at(53 + ox * 1.4, 31 + by + hy)
    ramp = "tell" if P["tell"] else "beye"
    for dx, dy, sh in ((0, 0, 0), (1, 0, 1), (0, 1, 1), (1, 1, 1)):
        g[(ex + dx, ey + dy)] = (ramp, sh)
    if P["tell"]:
        for dx, dy in ((-1, 0), (2, 0), (-1, 1), (2, 1), (0, -1), (1, -1), (0, 2), (1, 2)):
            g[(ex + dx, ey + dy)] = ("tell", 1)
    for k in range(-2, 4):
        g[(ex + k, ey - 2 + (k + 2) // 2)] = ("o",)
    nx, ny = c.at(62.5 + ox * 1.4, 42 + by + hy)
    g[(nx, ny)] = ("snout", 3)
    g[(nx, ny + 3)] = ("snout", 3)
    return g


BEASTS = {"bramble_boar": (72, 64, 1.06, 0, bramble_boar)}  # name: (w, h, scale, x offset, builder)
ANIMS = {"idle": 3, "tell": 3}


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
    for name in [a for a in sys.argv[1:] if not a.startswith("-")] or list(BEASTS):
        w, h, k, dx, fn = BEASTS[name]
        write(name, w, h, {a: [fn(Scaled(w, h, k, dx, h - 1), bpose(a, f)) for f in range(n)] for a, n in ANIMS.items()})
