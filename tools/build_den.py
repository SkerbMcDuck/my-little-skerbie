# Builds the home den backgrounds (ART_BRIEF §6), portrait 225x487, in neutral lighting
# (the time-of-day tint and lantern glow are separate overlays; the sky is a separate layer
# that shows through the transparent area above the treeline).
# Usage: python tools/build_den.py burrow   (look test; hideout and lair come later)
#        python tools/render.py art/source/home/den_burrow.json --out art/out/home/den_burrow --scale 2
#
# Layout (ART_BRIEF §6): top ~30% surface (forest floor, the huge trunk rising out of frame,
# the root door, a garden patch, room for the merchant cart and the overflow pile), middle
# ~50% the den hollowed out under the roots, bottom ~20% the deep roots and stone where the
# Delve crack opens later (its own sprite). Backgrounds have soft or no outlines, so the
# characters pop. Light comes from the top-left. All colours are from the §3 world palette.
import json, math, os, random, sys

TIER = sys.argv[1] if len(sys.argv) > 1 else "burrow"
assert TIER in ("burrow", "hideout", "lair"), "tier must be burrow, hideout or lair"
#   burrow:  a rough dirt hollow, bare roots, one candle (look approved by George, 2026-11-22)
#   hideout: stone-lined walls, root-carved shelves, a rug, a plank door in the root arch
#   lair:    carved stone pillars, iron fixtures, banners, a trophy mount, rune-lit wall glyphs,
#            flagstone floor, an iron-reinforced root door
# All three share the surface, the tree, the hollow's shape and the roots, so the den visibly
# upgrades in place. Buildables (bed, hearth, lanterns...) are separate sprites on the spots.
W, H = 225, 487
GROUND, DEN_TOP, DEN_FLOOR, DEEP = 136, 168, 372, 392   # key heights

PAL = {
    # far forest (slate) and near treeline
    "S": "#4d5e7a", "T": "#3b4a63", "U": "#2a3448",
    # moss and grass on the forest floor
    "G": "#557a5c", "H": "#3e5a46", "I": "#2c4234",
    # soil: dusky purple earth and charcoal
    "p": "#4a3a5c", "q": "#3a2d4a", "r": "#2a2036",
    "c": "#33303d", "d": "#23212b", "e": "#17151c",
    # bark and roots: dark wood with a warm lit edge
    "R": "#3b2a22", "W": "#7a5636", "B": "#8b7a4a",
    # teal shadow for cool depth in the deep roots
    "t": "#1f3d44", "u": "#2c5560",
    # candle: wax, flame (also the amber of the Lair's rune glyphs)
    "y": "#ffc8a8", "Y": "#ffd08a", "Z": "#ffb35c", "O": "#ff8a3d",
}
if TIER != "burrow":
    PAL.update({"i": "#5a5e66", "w": "#c9cfd6",       # iron fixtures, rivets
                "k": "#f2a0b0",                       # warm pink in the rug weave
                "b": "#bfae8c", "a": "#a8945e"})      # bone (trophy), worn cloth/leather
grid = [["." for _ in range(W)] for _ in range(H)]


def setp(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        grid[y][x] = c


def getp(x, y):
    return grid[y][x] if 0 <= x < W and 0 <= y < H else None


def inside(poly, x, y):
    px, py, hit = x + .5, y + .5, False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[i - 1]
        if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


def fill(poly, colour):
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    for y in range(max(0, int(min(ys))), min(H, int(max(ys)) + 1)):
        for x in range(max(0, int(min(xs))), min(W, int(max(xs)) + 1)):
            if inside(poly, x, y):
                setp(x, y, colour(x, y) if callable(colour) else colour)


def noise(x, y, scale, seed):
    # Smooth value noise in [0, 1): clustered patches instead of salt-and-pepper speckle.
    def h(ix, iy):
        return random.Random(ix * 7919 + iy * 104729 + seed * 31337).random()
    fx, fy = x / scale, y / scale
    ix, iy = int(math.floor(fx)), int(math.floor(fy))
    tx, ty = fx - ix, fy - iy
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    a, b = h(ix, iy) + (h(ix + 1, iy) - h(ix, iy)) * tx, h(ix, iy + 1) + (h(ix + 1, iy + 1) - h(ix, iy + 1)) * tx
    return a + (b - a) * ty


def root(points, w0, w1):
    # A thick, tapering root along a polyline: dark core, warm lit top-left edge, deep shadow below.
    pts = []
    for i in range(len(points) - 1):
        (x0, y0), (x1, y1) = points[i], points[i + 1]
        n = max(2, int(math.hypot(x1 - x0, y1 - y0)))
        pts += [(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n) for k in range(n)]
    total = len(pts)
    mask = {}
    for k, (cx, cy) in enumerate(pts):
        r = (w0 + (w1 - w0) * k / max(1, total - 1)) / 2
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                d = math.hypot(x + .5 - cx, y + .5 - cy)
                if d <= r:
                    lit = ((x + .5 - cx) * -0.6 + (y + .5 - cy) * -0.8) / max(r, 0.5)
                    mask[(x, y)] = max(mask.get((x, y), -9), lit)
    for (x, y), lit in mask.items():
        setp(x, y, "W" if lit > 0.55 else "R" if lit > -0.45 else "e")


# ---- 1. Surface: far forest silhouette, near treeline (the sky shows through above them) ----
rnd = random.Random(7)
# Two rows of conifer silhouettes: a far, darker row and a nearer, lighter one, each tree a
# tall pointed triangle with a stepped (tiered) edge, lit a touch on its left side.
for layer, (hmin, hmax, wmin, wmax, base, lit, body) in enumerate(((48, 78, 10, 16, GROUND, "U", "U"),
                                                                   (34, 60, 12, 20, GROUND, "S", "T"))):
    x = rnd.randint(-8, 0)
    while x < W + 8:
        hgt, half = rnd.randint(hmin, hmax), rnd.randint(wmin, wmax) / 2
        top = base - hgt
        for y in range(int(top), base):
            t = (y - top) / hgt
            tier = 1.6 * ((y - top) % 9) / 9                        # stepped branch tiers
            reach = half * t + tier * t
            for xx in range(int(x - reach), int(x + reach) + 1):
                setp(xx, y, lit if (layer and xx < x - reach * 0.4 and (y // 3) % 2 == 0) else body)
        x += rnd.randint(int(wmin * 0.7), int(wmax * 0.9))

# ---- 2. Soil everywhere below the ground line, with soft strata ----
for y in range(GROUND, H):
    for x in range(W):
        # Mostly one calm earth tone; broad soft patches (large-scale noise) and faint strata.
        n = noise(x, y, 18, 3) + 0.15 * noise(x, y, 5, 4)
        strata = (y + int(6 * noise(x, 0, 30, 14))) % 23 == 0
        if y >= DEEP:  # deep roots and stone: colder, darker, with only a hint of teal
            c = "t" if n > 1.05 else "d" if n > 0.5 else "e"
        else:
            c = "r" if strata or n < 0.35 else "p" if n > 1.0 else "q"
        setp(x, y, c)

# ---- 3. Forest floor: grass and moss along the top of the soil, with tufts ----
for x in range(W):
    lip = GROUND + int(2 * noise(x, 0, 6, 5))
    for y in range(GROUND - 3, lip + 4):
        if y < GROUND:
            if (x * 7 + y) % 5 == 0 and noise(x, y, 3, 6) > 0.45:  # grass tufts
                setp(x, y, "H")
        else:
            setp(x, y, "G" if y < lip + 1 else "H" if y < lip + 3 else "I")

# ---- 4. The huge trunk rising out of frame, its root flare spreading into the ground ----
trunk = [(84, 0), (146, 0), (150, 60), (154, 98), (168, 118), (186, 134), (198, 140),
         (150, 140), (140, 132), (88, 132), (76, 140), (34, 140), (50, 132), (68, 116), (78, 96), (80, 60)]


def bark(x, y):
    # Dark bark with long vertical grain; a warm edge only on the lit left side.
    streak = noise(x * 3, y * 0.25, 4, 8)
    edge = (x - 84) / 62
    if streak < 0.2:
        return "e"
    if edge < 0.12 and streak > 0.62:
        return "B"
    if edge < 0.35 and streak > 0.6:
        return "W"
    return "R" if edge < 0.8 or streak > 0.45 else "e"


fill(trunk, bark)
# The root door: a dark arch in the trunk's base, framed by a lip of root.
door = [(104, 134), (104, 116), (108, 108), (115, 104), (122, 108), (126, 116), (126, 134)]
fill(door, lambda x, y: "e" if y > 110 or noise(x, y, 2, 9) > 0.3 else "d")
root([(100, 135), (101, 116), (106, 106), (115, 101), (124, 106), (129, 116), (130, 135)], 4, 4)

# ---- 5. The den: a hollow under the roots, connected to the door by a shaft ----
den = [(16, 372), (12, 330), (16, 268), (30, 214), (58, 184), (92, 172), (134, 170), (170, 178),
       (196, 200), (210, 244), (214, 300), (211, 346), (206, 372)]
shaft = [(106, 134), (124, 134), (128, 176), (102, 176)]
hollow = set()
for poly in (den, shaft):
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    for y in range(int(min(ys)), int(max(ys)) + 1):
        for x in range(int(min(xs)), int(max(xs)) + 1):
            if inside(poly, x, y):
                hollow.add((x, y))


def rim(x, y, d):
    return any((x + dx, y + dy) not in hollow for dx in range(-d, d + 1) for dy in range(-d, d + 1))


for (x, y) in hollow:
    n = noise(x, y, 22, 12) + 0.12 * noise(x, y, 6, 13)
    if y >= DEN_FLOOR - 6:                      # packed dirt floor, lighter on top
        c = "q" if y < DEN_FLOOR - 3 else "r"
    elif rim(x, y, 2):                          # dark edge where the walls curve away
        c = "e"
    elif rim(x, y, 5):
        c = "d"
    else:                                       # the back wall: smooth dark earth, rare soft patches
        c = "c" if n > 1.04 else "q" if n < 0.14 else "d"
    setp(x, y, c)
for x in range(W):                              # floor edge line, where it meets the back wall
    if (x, DEN_FLOOR - 7) in hollow and (x, DEN_FLOOR - 6) in hollow:
        setp(x, DEN_FLOOR - 6, "p")

# ---- 5b. Hideout and Lair: stone lining (and in the Lair, a flagstone floor) ----
def dist_to_edge(x, y, cap):
    for d in range(1, cap + 1):
        if rim(x, y, d):
            return d
    return cap + 1


if TIER != "burrow":
    thick = 7 if TIER == "hideout" else 11
    for (x, y) in sorted(hollow):
        if (x, y) in set((px, py) for px, py in hollow if py < 178 and 100 <= px <= 130):
            continue  # leave the shaft as dug earth
        floor = y >= DEN_FLOOR - 6
        d = dist_to_edge(x, y, thick)
        if d > thick and not (floor and TIER == "lair"):
            continue
        # Bricks: 5 px rows, 9-11 px long, staggered; dark mortar; lit on the top-left.
        bh = 5 if not floor else 3
        row = y // bh
        bw = 10 if not floor else 14
        bx = (x + (row % 2) * bw // 2) % bw
        if y % bh == 0 or bx == 0:
            setp(x, y, "e")
        else:
            n = noise(x // 4, row, 2, 40 + row)
            setp(x, y, "S" if (y % bh == 1 or bx == 1) and n > 0.35 else "U" if n < 0.25 else "T")

# ---- 6. Bare roots: through the soil, across the den ceiling and down the walls ----
ROOTS = [
    ([(88, 138), (70, 150), (44, 166), (22, 196), (10, 236)], 8, 3),
    ([(150, 138), (172, 152), (196, 172), (214, 206)], 8, 3),
    ([(110, 140), (98, 160), (84, 176), (60, 186), (40, 200)], 5, 2),
    ([(132, 140), (148, 162), (168, 182), (184, 206), (188, 232)], 6, 2),
    ([(62, 182), (66, 196), (62, 214)], 3, 1.2),      # dangling root tips in the den
    ([(150, 176), (146, 192), (150, 206)], 3, 1.2),
    ([(112, 172), (110, 186)], 2.4, 1),
    ([(4, 300), (20, 318), (14, 352), (24, 380), (10, 420)], 6, 3),
    ([(221, 290), (208, 330), (216, 368), (204, 410)], 6, 3),
    ([(40, 392), (70, 410), (108, 418), (150, 412), (186, 398)], 7, 4),   # deep roots under the floor
    ([(16, 440), (48, 452), (60, 478), (90, 486)], 6, 3),
    ([(200, 440), (176, 462), (150, 470), (128, 486)], 6, 3),
]
for pts, w0, w1 in ROOTS:
    root(pts, w0, w1)
# Root rungs down the shaft, so he can climb up to the door.
for y in (146, 156, 166):
    root([(104, y), (126, y + 1)], 2.6, 2.6)

# ---- 7. Stones in the deep roots ----
srnd = random.Random(21)
for _ in range(16):
    cx, cy, r = srnd.randint(8, W - 8), srnd.randint(DEEP + 6, H - 6), srnd.uniform(3, 7)
    for y in range(int(cy - r), int(cy + r) + 1):
        for x in range(int(cx - r * 1.4), int(cx + r * 1.4) + 1):
            d = math.hypot((x + .5 - cx) / 1.4, y + .5 - cy)
            if d <= r and getp(x, y) not in ("R", "W", "e"):
                lit = ((x + .5 - cx) * -0.6 + (y + .5 - cy) * -0.8) / r
                setp(x, y, "S" if lit > 0.5 else "T" if lit > -0.3 else "U")

if TIER == "burrow":
    # ---- 8. One candle on a dirt ledge in the left wall (the Burrow's only light) ----
    fill([(26, 300), (50, 300), (48, 305), (28, 305)], "p")          # ledge
    fill([(36, 290), (40, 290), (40, 300), (36, 300)], "y")          # wax
    for (x, y), c in {(38, 288): "Z", (38, 287): "Y", (37, 289): "O", (38, 289): "Y", (39, 289): "O",
                      (38, 286): "Y", (38, 285): "Z"}.items():
        setp(x, y, c)


def plank_door(iron):
    # Vertical planks filling the root arch; the Lair's door adds iron bands and rivets.
    for (x, y) in [(x, y) for y in range(104, 135) for x in range(104, 127) if inside(door, x, y)]:
        seam = (x - 104) % 5 == 0
        setp(x, y, "e" if seam else "W" if (x - 104) % 5 == 1 else "R")
    if iron:
        for by in (112, 125):
            for x in range(103, 128):
                if inside(door, x, by) or inside(door, x, by + 1):
                    setp(x, by, "w" if x % 6 == 2 else "i")
                    setp(x, by + 1, "i" if x % 6 != 2 else "w")
        setp(122, 119, "Z")  # a little iron ring pull, catching the light
        setp(123, 119, "i")


def shelf(x0, x1, y):
    # A shelf carved from a root running along the wall, with a little root bracket under it.
    root([(x0, y), (x1, y)], 4, 4)
    root([(x0 + 3, y + 2), (x0 + 6, y + 8)], 2.4, 1.6)
    root([(x1 - 3, y + 2), (x1 - 6, y + 8)], 2.4, 1.6)


if TIER == "hideout":
    plank_door(iron=False)
    shelf(26, 70, 252)
    shelf(156, 202, 236)
    # A woven rug lying on the floor (side view, so a low strip): dusky body, a pink and
    # amber woven band along the middle, dark edges, and a fringe at each end.
    ry0, ry1 = DEN_FLOOR - 9, DEN_FLOOR - 4
    for y in range(ry0, ry1 + 1):
        for x in range(56, 172):
            if y in (ry0, ry1):
                c = "r"
            elif y == ry0 + 2 or y == ry0 + 3:
                c = "Z" if (x // 3) % 4 == 0 else "k" if (x // 3) % 4 == 2 else "p"
            else:
                c = "p" if y == ry0 + 1 else "q"
            setp(x, y, c)
    for x in list(range(52, 56)) + list(range(172, 176)):
        for y in range(ry0 + 1, ry1, 2):
            setp(x, y, "a")

if TIER == "lair":
    plank_door(iron=True)
    # Carved stone pillars on both sides, with a capital and a base; iron rings bolted on.
    for px in (30, 181):
        for y in range(206, DEN_FLOOR - 6):
            for x in range(px, px + 15):
                if (x, y) in hollow or x in (px, px + 14):
                    edge = x - px
                    groove = edge in (4, 10)
                    c = "e" if edge in (0, 14) else "U" if groove else "S" if edge < 4 else "T"
                    if y < 214 or y > DEN_FLOOR - 15:      # capital and base blocks, wider
                        c = "S" if y in (206, DEN_FLOOR - 14) else "T" if edge < 12 else "U"
                    setp(x, y, c)
        for ry in (252, 316):                              # iron rings
            for dx, dy in ((5, 0), (6, 0), (7, 0), (8, 0), (9, 0), (5, 1), (9, 1), (5, 2), (9, 2), (6, 3), (7, 3), (8, 3)):
                setp(px + dx, ry + dy, "w" if dy == 0 else "i")
    # Banners hanging from iron rods near the ceiling, with a pointed tail and an amber emblem.
    for bx in (60, 148):
        for x in range(bx - 2, bx + 20):
            setp(x, 214, "i")
        for y in range(215, 268):
            for x in range(bx, bx + 17):
                tail = y > 258 and abs(x - (bx + 8)) > (268 - y)
                if not tail:
                    setp(x, y, "e" if x in (bx, bx + 16) else "p" if x < bx + 6 else "q")
        for dx, dy in ((8, 228), (7, 229), (9, 229), (6, 230), (10, 230), (8, 231), (8, 232), (7, 236), (8, 236),
                       (9, 236), (8, 237), (8, 238)):
            setp(bx + dx, dy, "Z")
    # A trophy mount on the back wall: a wooden shield-plaque with a horned skull.
    fill([(100, 222), (126, 222), (126, 238), (113, 248), (100, 238)], "R")
    fill([(101, 223), (125, 223), (125, 237), (113, 246), (101, 237)], "W")
    fill([(108, 228), (118, 228), (119, 236), (113, 241), (107, 236)], "b")
    root([(108, 229), (102, 222), (100, 216)], 2.6, 1.2)   # horns (drawn like curved roots, then recoloured)
    root([(118, 229), (124, 222), (126, 216)], 2.6, 1.2)
    for y in range(214, 232):
        for x in range(98, 128):
            if getp(x, y) in ("W", "R") and (y < 223 or not inside([(100, 222), (126, 222), (126, 238), (113, 248), (100, 238)], x, y)):
                setp(x, y, "b" if getp(x, y) == "W" else "a")
    for (x, y) in ((110, 232), (111, 232), (115, 232), (116, 232)):
        setp(x, y, "e")                                    # eye sockets
    # Rune glyphs carved into the stone lining, glowing amber.
    for gx, gy in ((22, 280), (200, 268), (60, 196), (166, 196), (24, 340), (202, 334)):
        for dx, dy in ((0, 0), (0, 1), (0, 2), (0, 3), (-1, 1), (1, 1), (-1, 3), (1, 3)):
            setp(gx + dx, gy + dy, "Z" if dy % 2 else "O")

# Where the buildables and the crack go (ART_BRIEF §6 / BUILD_SPEC §7), for the game to read.
SPOTS = {
    "door": [115, 120], "garden": [190, 132], "merchant_cart": [30, 132], "overflow_pile": [148, 134],
    "bed": [44, 372], "pantry": [70, 300], "workbench": [180, 372], "chest": [140, 372],
    "walls_traps": [115, 176], "training": [96, 372], "hearth": [112, 340], "decor": [38, 300],
    "chalkboard": [196, 300], "blueprint": [166, 240], "radio": [150, 300], "crack": [112, 428],
}
os.makedirs("art/source/home", exist_ok=True)
json.dump({"width": W, "height": H, "fps": 1, "palette": PAL, "dye_zones": {}, "attach": {},
           "spots": SPOTS, "animations": {TIER: [["".join(r) for r in grid]]}},
          open(f"art/source/home/den_{TIER}.json", "w"))
print(f"den_{TIER}: {W}x{H}")


# ---- SKB-CRACK: the Cave Delve entrance in the deep roots (its own 48x24 sprite) ----
# "hidden": a faint seam in the stone; "open" (4-frame loop): a jagged split with a glow
# pulsing up from below. It sits on the "crack" spot, centred. Same in every den tier.
def crack():
    CW, CH = 48, 24
    cpal = {"e": "#17151c", "d": "#23212b", "U": "#2a3448", "T": "#3b4a63",
            "O": "#ff8a3d", "Z": "#ffb35c", "Y": "#ffd08a", "y": "#ffc8a8"}
    path = [(2, 12), (8, 10), (12, 13), (18, 9), (23, 12), (27, 8), (32, 12), (37, 10), (41, 13), (46, 11)]

    def line_pts():
        pts = []
        for (x0, y0), (x1, y1) in zip(path, path[1:]):
            n = max(abs(x1 - x0), abs(y1 - y0))
            pts += [(round(x0 + (x1 - x0) * k / n), round(y0 + (y1 - y0) * k / n)) for k in range(n)]
        return pts

    pts = line_pts()
    hidden = {}
    for (x, y) in pts:  # a thin dark seam with a slightly lifted stone edge above it
        hidden[(x, y)] = "e"
        hidden[(x, y - 1)] = "T"
    frames = [hidden]
    opened = []
    for f in range(4):
        g = {}
        for k, (x, y) in enumerate(pts):
            # A dark jagged split, widest in the middle; only a thin glow deep inside it.
            half = 2 if 10 < x < 38 else 1 if 4 < x < 44 else 0
            pulse = (f + k // 6) % 4
            for dy in range(-half - 1, half + 2):
                if abs(dy) == half + 1:
                    c = "T" if dy < 0 else "U"                  # cracked stone lip, lit above
                elif dy == 0 and half:
                    c = "Z" if pulse in (0, 1) else "O"         # the glow line, slowly pulsing
                elif abs(dy) == 1 and half == 2 and pulse == 0:
                    c = "O"                                     # it swells a little at its brightest
                else:
                    c = "e" if abs(dy) == half else "d"
                g[(x, y + dy)] = c
            if k % 11 == 3 and 10 < x < 38 and f % 2 == 0:      # an occasional ember drifting up
                g[(x, y - half - 3 - (f // 2))] = "O"
        opened.append(g)
    rows = lambda g: ["".join(g.get((x, y), ".") for x in range(CW)) for y in range(CH)]
    json.dump({"width": CW, "height": CH, "fps": 6, "palette": cpal, "dye_zones": {}, "attach": {},
               "anchor": [CW // 2, CH // 2],
               "animations": {"hidden": [rows(frames[0])], "open": [rows(g) for g in opened]}},
              open("art/source/home/crack.json", "w"))


if TIER == "burrow":
    crack()
