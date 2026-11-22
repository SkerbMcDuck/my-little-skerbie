# Builds the baby Skerbie (32x32) idle + blink frames as pixel grids -> JSON.
import json, math

W = H = 32
PAL = {
    "o": "#0f0d14",
    "1": "#4a4552", "2": "#2a2630", "3": "#1a1720", "4": "#0b0a0e",   # main fur
    "5": "#8a8494", "6": "#615b6b", "7": "#433e4c", "8": "#2c2833",   # accent fur
    "e": "#ff9a8a", "E": "#ff3d3d", "f": "#b81f2e", "F": "#6e0f1c",   # eye glow
}
LX, LY = -0.6, -0.8  # light from top-left

def ell(cx, cy, rx, ry, rot=0.0):
    c, s = math.cos(rot), math.sin(rot)
    pts = {}
    for y in range(-4, H):
        for x in range(W):
            dx, dy = x + .5 - cx, y + .5 - cy
            u, v = dx * c + dy * s, -dx * s + dy * c
            nx, ny = u / rx, v / ry
            if nx * nx + ny * ny <= 1:
                # normal back in screen space
                pts[(x, y)] = (nx * c - ny * s, nx * s + ny * c)
    return pts

def tone(n, dark=0):
    nx, ny = n
    lit = nx * LX + ny * LY
    r = math.hypot(nx, ny)
    t = 2
    if lit < -0.25: t = 3
    if lit < -0.6 and r > 0.7: t = 4
    if lit > 0.6 and r > 0.65: t = 1
    return min(4, t + dark)

def frame(bob=0, ear=0, tail=0, eyes="open"):
    g, layer = {}, {}
    def paint(pts, part, dark=0, acc=None):
        for p, n in pts.items():
            t = tone(n, dark)
            g[p] = str(t + 4) if (acc and acc(p)) else str(t)
            layer[p] = part
    hy = 12.5 + bob
    # far side (darker)
    paint(ell(13.4, 5.2 + bob, 2.5, 5.6, -0.6), "farear", dark=1)
    for lx in (6.0, 15.6):
        paint(ell(lx, 25.2, 1.9, 3.3), "farleg", dark=1)
    paint(ell(2.8, 17.0 + tail * 0.6, 2.2, 2.6, -0.5), "tail",
          acc=lambda p: p[1] <= 16 + tail and p[0] <= 3)
    paint(ell(11.5, 21.0 + bob * 0.5, 8.8, 6.0), "body",
          acc=lambda p: p[1] >= 24 and 6 <= p[0] <= 17)
    for lx in (8.6, 18.2):
        paint(ell(lx, 25.6, 2.2, 3.5), "leg")
    ex, ey = 19.4 - ear * 0.7, 4.2 + bob
    paint(ell(ex, ey, 3.3, 6.0, -0.25 - ear * 0.15), "ear",
          acc=lambda p: (p[0] + .5 - ex) ** 2 / 1.3 + (p[1] + .5 - (ey + 1.2)) ** 2 / 7 < 1)
    paint(ell(19.4, hy, 7.6, 6.8), "head",
          acc=lambda p: p[1] >= hy + 4.0 and 15 <= p[0] <= 22)
    paint(ell(25.2, hy + 2.4, 2.4, 1.8), "muzzle")
    for (x, y), part in list(layer.items()):
        nb = [layer.get((x + dx, y + dy)) for dx, dy in ((0, 1), (-1, 0), (0, -1), (1, 0))]
        if part == "head" and ("body" in nb[:2] or "tail" in nb[:2]):
            g[(x, y)] = "4"
        if part == "leg" and ("farleg" in nb or nb[1] == "body") and y > 25:
            g[(x, y)] = "4"
        if part == "ear" and nb[1] == "farear":
            g[(x, y)] = "4"
    filled = set(g)
    for (x, y) in filled:
        if any((x + dx, y + dy) not in filled for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            g[(x, y)] = "o"
    for lx in (8, 18):
        if (lx, 28) in g: g[(lx, 28)] = "o"
    nx0, ny0 = 18, int(round(hy - 3))
    if eyes == "open":
        near = [".EEE.", "EeeEE", "EeFEf", "EEFff", ".fff."]
        far = ["EE", "eF", "EF", "ff"]
    elif eyes == "half":
        near = ["33333", "ooooo", "EEFEf", "EEFff", ".fff."]
        far = ["33", "oo", "EF", "ff"]
    else:
        near = ["33333", "22222", "ooooo", "23332", ".222."]
        far = ["33", "22", "oo", "22"]
    for j, row in enumerate(near):
        for i, c in enumerate(row):
            if c != ".": g[(nx0 + i, ny0 + j)] = c
    for j, row in enumerate(far):
        for i, c in enumerate(row):
            g[(24 + i, ny0 + j)] = c
    my = int(round(hy + 2))
    g[(27, my)] = "o"
    g[(25, my + 2)] = "o"; g[(26, my + 2)] = "o"
    return ["".join(g.get((x, y - 2), ".") for x in range(W)) for y in range(H)]

idle = [frame(), frame(bob=-1), frame(bob=-1, ear=1, tail=-1), frame(ear=1, tail=-1)]
blink = [frame(eyes="half"), frame(eyes="closed")]

data = {
    "width": W, "height": H, "fps": 10, "palette": PAL,
    "dye_zones": {"main_fur": ["1", "2", "3", "4"], "accent_fur": ["5", "6", "7", "8"],
                  "eye_glow": ["e", "E", "f", "F"], "smoke": ["s", "S", "t", "T"]},
    "attach": {},
    "animations": {"idle": idle, "blink": blink},
}
json.dump(data, open("art/source/skerbie/baby.json", "w"), indent=1)
print("\n".join(idle[0]))
