# Builds the Skerbie egg (24x32): wobble [3], crack [4], hatch [5] -> JSON.
# Same angular house style as the approved baby: a faceted charcoal shell
# with flat-plane shading and red ember-glow cracks. Smoke is a separate effect.
# Run: python tools/build_egg.py, then python tools/render.py art/source/skerbie/egg.json --out art/out/skerbie/egg
import json

W, H = 24, 32
PAL = {
    "o": "#0f0d14",                                                   # outline
    "h": "#4a4552", "a": "#33303d", "b": "#23212b", "c": "#17151c",   # charcoal shell (never dyed)
    "e": "#ff9a8a", "E": "#ff3d3d", "f": "#b81f2e", "F": "#6e0f1c",   # ember glow (his eye-glow ramp)
}
LX, LY = -0.6, -0.8  # light from top-left
SHELL = [(12, 0.5), (17, 2.5), (20.5, 8), (22.5, 15), (22.5, 21), (20.5, 26.5), (16.5, 30.5),
         (7.5, 30.5), (3.5, 26.5), (1.5, 21), (1.5, 15), (3.5, 8), (7, 2.5)]
# The crack line: one y per column, a jagged zigzag across the middle.
CRACK_Y = [15, 15, 14, 13, 14, 15, 16, 15, 14, 13, 12, 13, 14, 15, 14, 13, 14, 15, 16, 15, 14, 14, 14, 14]
# Columns the crack has reached at each stage (it spreads out from the right).
STAGES = [range(14, 18), range(10, 21), range(4, 22), range(1, 23)]
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def inside(poly, x, y):
    px, py, hit = x + .5, y + .5, False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[i - 1]
        if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


def shell():
    # Flat faceted shading: straight thresholds on a top-left light direction.
    g = {}
    for y in range(H):
        for x in range(W):
            if inside(SHELL, x, y):
                nx, ny = (x + .5 - 12) / 11, (y + .5 - 15.5) / 15.5
                lit = nx * LX + ny * LY
                g[(x, y)] = "h" if lit > 0.55 else "a" if lit > 0.0 else "b" if lit > -0.5 else "c"
    # A sharp glint on the lit facet.
    for p in ((6, 6), (6, 7), (7, 5), (5, 8)):
        g[p] = "h"
    return g


def outline(g, groups=None):
    # Outline every pixel that touches empty space (or a different piece).
    out = dict(g)
    for (x, y) in g:
        for dx, dy in N4:
            q = (x + dx, y + dy)
            if q not in g or (groups and groups.get(q) != groups.get((x, y))):
                out[(x, y)] = "o"
                break
    return out


def add_crack(g, cols, bright):
    core, rim = ("e", "E") if bright else ("E", "f")
    for x in cols:
        y = CRACK_Y[x]
        if (x, y) in g and g[(x, y)] != "o":
            g[(x, y)] = core
            if (x, y + 1) in g and g[(x, y + 1)] != "o":
                g[(x, y + 1)] = rim


def wobble_shift(g, k):
    # Lean the egg by shearing it: the base stays put, the top tips k*2 px.
    return {(x + round(k * 2 * (30 - y) / 30), y): c for (x, y), c in g.items()}


def to_rows(g):
    return ["".join(g.get((x, y), ".") for x in range(W)) for y in range(H)]


def resting(k):
    g = shell()
    for x in STAGES[0]:  # a faint ember crack is always there
        g[(x, CRACK_Y[x])] = "F"
    return outline(wobble_shift(g, k))  # lean first, then outline, so the edges stay clean


wobble = [to_rows(resting(k)) for k in (-1, 0, 1)]

crack = []
for i, cols in enumerate(STAGES):
    g = outline(shell())
    add_crack(g, cols, bright=i >= 2)
    if i == 3:  # a branch splits off downward
        for p in ((7, 17), (7, 18), (8, 19), (17, 16), (16, 17)):
            if g.get(p) not in (None, "o"):
                g[p] = "E"
    crack.append(to_rows(g))


def hatch_frame(lift, tilt, eyes, top_gone=False, sink=0):
    base = shell()
    top = {p: c for p, c in base.items() if p[1] < CRACK_Y[p[0]]}
    bot = {p: c for p, c in base.items() if p[1] > CRACK_Y[p[0]]}
    # The broken rim of the lower half glows from inside.
    for x in range(W):
        ys = [y for (px, y) in bot if px == x]
        if ys:
            bot[(x, min(ys))] = "E"
    # Shift whole rows (not single pixels) so the tilted lid stays solid.
    moved = {} if top_gone else {(x + round(tilt * (14 - y) / 7), y - lift): c
                                 for (x, y), c in top.items()}
    groups = {p: "b" for p in bot}
    groups.update({p: "t" for p in moved})
    g = outline({**bot, **moved}, groups)
    rim = {}
    for x in range(W):
        ys = [y for (px, y) in bot if px == x]
        if ys:
            rim[x] = min(ys)
    # Dark inside of the egg showing through the gap.
    # Fill each column from the rim up to the lid, so the gap is one clean dark band.
    for x, ry in rim.items():
        lid = [y for (px, y) in moved if px == x]
        if top_gone or not lid or not 2 <= x <= 21:
            continue
        for y in range(max(lid) + 1, ry):
            g[(x, y)] = "o"
    if top_gone:  # two sharp ear tips and a head peek over the broken rim
        head = [(5.5, 17), (6.5, 8 + sink), (9.5, 11.5 + sink), (14.5, 11.5 + sink),
                (17.5, 8 + sink), (18.5, 17)]
        for y in range(H):
            for x in range(W):
                if inside(head, x, y) and (x, y) not in bot:
                    g[(x, y)] = "o"
    for x, ry in rim.items():  # re-light the rim after outlining
        if 2 <= x <= 21:
            g[(x, ry)] = "e" if lift or top_gone else "E"
    if eyes:  # his narrowed glare, sloping down toward the middle
        ey = rim[12] - 1 if not top_gone else 13 + sink // 2
        for x0, row in ((7, "eEE"), (14, "EEe")):
            for i, c in enumerate(row):
                g[(x0 + i, ey)] = c
        g[(9, ey + 1)] = "f"
        g[(14, ey + 1)] = "f"
    return to_rows(g)


hatch = [
    hatch_frame(0, 0, False),
    hatch_frame(2, 0, True),
    hatch_frame(4, 1, True),
    hatch_frame(0, 0, True, top_gone=True, sink=3),
    hatch_frame(0, 0, True, top_gone=True),
]

data = {
    "width": W, "height": H, "fps": 10, "palette": PAL,
    "dye_zones": {},  # the egg always uses the default look
    "attach": {},
    "animations": {"wobble": wobble, "crack": crack, "hatch": hatch},
}
json.dump(data, open("art/source/skerbie/egg.json", "w"), indent=1)
print("\n".join(crack[3]))
