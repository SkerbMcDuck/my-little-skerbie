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
from build_enemies import Canvas, R, ik, polar, lerp, rot, boot  # noqa: E402

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


def bramble_boar(c, P):  # 64x64: a hulking boar wrapped in bramble vines, a thorn crest and big tusks
    G = 63
    ox, by = P["lean"], P["bob"] + P["crouch"]
    hy = P["head"]
    T = lambda pts, k=1.0: [(x + ox * k, y + by) for x, y in pts]
    # far legs (darker)
    for top, fx, which in (((41, 47), 42, 1), ((15, 47), 15, 3)):
        ft = (fx + P["legs"][which], G - 1)
        c.stick((top[0] + ox, top[1] + by), ft, 7, 5.5, "boar", dark=1)
        c.poly([(ft[0] - 3, ft[1] - 3), (ft[0] + 3.5, ft[1] - 3), (ft[0] + 3.5, ft[1] + 1), (ft[0] - 3, ft[1] + 1)], "hoof", dark=1)
    # little curled vine tail
    c.stick((10 + ox, 40 + by), (5 + ox, 37 + by - P["sway"]), 3, 2, "moss")
    c.stick((5 + ox, 37 + by - P["sway"]), (4 + ox, 42 + by), 2.4, 1.6, "moss")
    # body: a heavy barrel with a high humped shoulder, sloping down to a small rump
    c.poly(T([(8, 47), (10, 38), (18, 32), (30, 25), (40, 21), (48, 25), (52, 35), (50, 48), (38, 53), (20, 53), (11, 51)]), "boar")
    for x in range(14, 48, 3):                                                   # bristle tufts along the belly
        c.px(x + ox, 52 + by + (x % 2), "boar", 3)
    # vines wrapping the flank, with small leaves
    for pts in (((22, 31), (26, 41), (22, 52)), ((35, 25), (38, 38), (34, 52))):
        pts = T(pts)
        c.stick(pts[0], pts[1], 2.2, 2.2, "moss", dark=1)
        c.stick(pts[1], pts[2], 2.2, 2.2, "moss", dark=1)
        c.blob(pts[1][0] + 2, pts[1][1] - 1, 2, 1.4, "moss")
    # near legs
    for top, fx, which in (((45, 47), 47, 0), ((19, 48), 20, 2)):
        ft = (fx + P["legs"][which], G - 1)
        c.stick((top[0] + ox, top[1] + by), ft, 8, 6, "boar")
        c.poly([(ft[0] - 3.5, ft[1] - 3), (ft[0] + 4, ft[1] - 3), (ft[0] + 4, ft[1] + 1), (ft[0] - 3.5, ft[1] + 1)], "hoof")
    # head: a long wedge sloping down from the hump to a big pink snout disc
    hk = 1.4
    H_ = lambda pts: [(x + ox * hk, y + by + hy) for x, y in pts]
    c.poly(H_([(47, 27), (42, 18), (51, 25)]), "boar")                                # ear
    c.poly(H_([(43, 27), (51, 27), (57, 34), (62, 43), (62, 50), (56, 53), (49, 50), (44, 42)]), "boar")
    c.poly(H_([(49, 48), (57, 50), (56, 54), (50, 53)]), "boar", dark=1)             # jaw
    c.poly(H_([(58, 41), (63.5, 42), (63.5, 52), (58.5, 52)]), "snout")
    # tusks: thick curved bone sweeping up beside the snout
    a, b, e = H_([(50, 53), (56, 50), (58, 40)])
    c.stick(a, b, 4.6, 3.8, "bone")
    c.stick(b, e, 3.8, 1.6, "bone")
    # bramble crest: a ridge of thorny vines along the spine, thorns fanning up and back
    sway = P["sway"]
    for i, (x, y) in enumerate(((14, 33), (20, 29), (26, 26), (32, 23), (38, 21), (44, 22))):
        x, y = x + ox, y + by
        for k, ln in ((-1, 7), (0, 9), (1, 6)):
            tip = polar((x, y - 1), -105 + k * 28 - sway * 5, ln + (i % 2) * 2)
            c.stick((x, y - 1), tip, 3.4, 1.2, "bone")
        c.blob(x, y, 4.2, 3.2, "moss", dark=(i % 2))
    for x, y in ((23, 27), (36, 22), (16, 32)):
        c.blob(x + ox, y + by, 1.8, 1.6, "fung")
    g = c.finish()
    # brow and eye (amber, or white-hot on the tell frame), nostrils
    ex, ey = int(round(53 + ox * hk)), int(round(33 + by + hy))
    ramp = "tell" if P["tell"] else "beye"
    g[(ex, ey)] = (ramp, 0)
    g[(ex + 1, ey)] = (ramp, 1)
    if P["tell"]:
        for dx, dy in ((-1, 0), (2, 0), (0, -1), (1, -1), (0, 1), (1, 1)):
            g[(ex + dx, ey + dy)] = ("tell", 1)
    for x in range(ex - 2, ex + 3):
        g[(x, ey - 1 - (1 if P["tell"] else 0))] = ("o",)
    nx, ny = int(round(62 + ox * hk)), int(round(45 + by + hy))
    g[(nx, ny)] = ("snout", 3)
    g[(nx, ny + 3)] = ("snout", 3)
    return g


BEASTS = {"bramble_boar": (64, 64, bramble_boar)}
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
        w, h, fn = BEASTS[name]
        write(name, w, h, {a: [fn(Canvas(w, h), bpose(a, f)) for f in range(n)] for a, n in ANIMS.items()})
