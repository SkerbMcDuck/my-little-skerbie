# Builds the item icons (ART_BRIEF §13): 24x24 icons that sit inside one of three rarity frames.
# Usage: python tools/build_items.py [--look]
#        then render each art/source/items/<file>.json with tools/render.py
#
#   frames.json         the 3 rarity frames in one row: wood (common), silver (rare), gold (epic; the gold
#                       frame also gets a soft glow layer, art/out/items/frames/glow.png, for additive blending)
#   icons_<group>.json  one row of icons per group; "icon_names" lists them in order, "rarity" gives each one's
#                       usual frame. An icon is drawn in the frame's 18x18 window (pixels 3..20), so the game
#                       draws the frame first and the icon on top at the same position.
# Weapon icons are made from the gear weapons' own shapes (tools/build_weapons.py) laid diagonally, so the
# icon always matches what he holds. Everything else is drawn here in the house style: faceted shading lit
# from the top-left, dark outline, §3 colours.
import json, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_enemies import Canvas, R, colour, rot  # noqa: E402

OUT = "art/source/items"
os.makedirs(OUT, exist_ok=True)
LOOK = "--look" in sys.argv
R.update({
    "wood":   ["#a8945e", "#7a5636", "#3b2a22", "#17151c"],
    "silver": ["#ffffff", "#c9cfd6", "#8a8494", "#5a5e66"],
    "goldf":  ["#ffe08a", "#f2c14e", "#a8643a", "#3b2a22"],
    "leath":  ["#a8643a", "#7a5636", "#3b2a22", "#17151c"],
    "cloth":  ["#4a3a5c", "#3a2d4a", "#2a2036", "#17151c"],
    "glass":  ["#cfe9ff", "#9fc9f0", "#4d5e7a", "#2a3448"],
    "potion": ["#ffc8a8", "#f2a0b0", "#4a3a5c", "#2a2036"],        # health potion: rosy
    "tonic":  ["#ffe08a", "#ffb347", "#ff7a1a", "#c2410c"],        # power tonic: fiery
    "moonc":  ["#f2f9ff", "#cfe9ff", "#9fc9f0", "#4d5e7a"],
    "cap":    ["#8ff0e6", "#2ec4b6", "#178f86", "#1f3d44"],        # glowcap
    "stem":   ["#bfae8c", "#a8945e", "#8b7a4a", "#3b2a22"],
    "pouch":  ["#a8643a", "#7a5636", "#3b2a22", "#17151c"],
    "gold":   ["#ffe08a", "#f2c14e", "#a8643a", "#3b2a22"],
    "bone":   ["#bfae8c", "#a8945e", "#8b7a4a", "#3b2a22"],
    "iron":   ["#c9cfd6", "#5a5e66", "#33303d", "#17151c"],
    "mind":   ["#e2b8ff", "#c77dff", "#9b4dff", "#6a2cc9"],
})


def write(name, frames, extra=None):
    pal, inv = {"o": "#0f0d14"}, {("o",): "o"}
    chars = iter("abcdfghijklmnpqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
    for fr in frames:
        for tok in fr.values():
            if tok not in inv:
                col = tok if isinstance(tok, str) else colour(tok)
                hit = next((k for k, v in pal.items() if v == col), None)
                if hit is None:
                    hit = next(chars)
                    pal[hit] = col
                inv[tok] = hit
    rows = [["".join(inv[fr[(x, y)]] if (x, y) in fr else "." for x in range(24)) for y in range(24)] for fr in frames]
    d = {"width": 24, "height": 24, "fps": 1, "palette": pal, "dye_zones": {}, "attach": {},
         "animations": {name.split("_", 1)[-1]: rows}}
    d.update(extra or {})
    json.dump(d, open(f"{OUT}/{name}.json", "w"))
    print("wrote", name)


# ============================================================================ rarity frames
def frame(kind):
    ramp = {"common": "wood", "rare": "silver", "epic": "goldf"}[kind]
    g = {}
    for y in range(24):
        for x in range(24):
            edge = min(x, y, 23 - x, 23 - y)
            if edge > 2:                                                    # a tinted backing panel behind the icon
                panel = {"common": "#3b2a22", "rare": "#2a3448", "epic": "#3a2d4a"}[kind]
                g[(x, y)] = panel if (x + y) % 2 or edge > 3 else "#23212b"
                continue
            if (x in (0, 23) and y in (0, 1, 22, 23)) or (y in (0, 23) and x in (0, 1, 22, 23)):
                continue                                                    # rounded corners
            if edge == 0:
                g[(x, y)] = ("o",)
            elif edge == 1:
                g[(x, y)] = (ramp, 0 if (x < 12 and y < 12 and (x == 1 or y == 1)) else 1 if (x == 1 or y == 1) else 2)
            else:
                g[(x, y)] = (ramp, 2 if (x == 2 or y == 2) else 3)
    if kind == "common":                                                    # wood grain and a couple of nails
        for x in (6, 13, 19):
            g[(x, 1)] = ("wood", 2)
            g[(x, 22)] = ("wood", 3)
        for p in ((2, 2), (21, 2), (2, 21), (21, 21)):
            g[p] = ("iron", 1)
    if kind == "rare":                                                      # rivets
        for p in ((2, 2), (21, 2), (2, 21), (21, 21)):
            g[p] = ("silver", 0)
    if kind == "epic":                                                      # gem studs at the corners
        for p in ((2, 2), (21, 2), (2, 21), (21, 21)):
            g[p] = ("mind", 1)
        for x in (11, 12):
            g[(x, 1)] = ("goldf", 0)
    return g


# ============================================================================ weapon icons from the gear shapes
def weapon_icon(wname):
    src = open("tools/build_weapons.py", encoding="utf-8").read()
    ns = {}
    exec(src.split('os.makedirs("art/source/gear"')[0], ns)                 # just the weapon shapes and render(), no files
    parts = ns["WEAPONS"][wname]
    for scale in [1.0 - k * 0.05 for k in range(12)]:
        rows = ns["render"](parts, -45, 48, scale, 1.0)
        cells = [(x, y) for y, r in enumerate(rows) for x, ch in enumerate(r) if ch != "."]
        xs, ys = [c[0] for c in cells], [c[1] for c in cells]
        if max(xs) - min(xs) < 18 and max(ys) - min(ys) < 18:
            break
    ox = 3 + (18 - (max(xs) - min(xs) + 1)) // 2 - min(xs)
    oy = 3 + (18 - (max(ys) - min(ys) + 1)) // 2 - min(ys)
    pal = ns["PAL"]
    return {(x + ox, y + oy): pal[rows[y][x]] for (x, y) in cells}


# ============================================================================ drawn icons
def icon(name):
    c = Canvas(24, 24)
    if name == "leather_vest":
        c.poly([(7, 5), (10, 4), (12, 7), (14, 4), (17, 5), (18, 19), (12, 20), (6, 19)], "leath")
        c.poly([(11.5, 7), (12.5, 7), (12.5, 19), (11.5, 19)], "leath", dark=2)
        g = c.finish()
        for y in (9, 12, 15):
            g[(11, y)] = ("iron", 0)
            g[(13, y)] = ("iron", 0)
        return g
    if name == "moon_coin":
        c.blob(12, 12, 7.5, 7.5, "moonc")
        g = c.finish()
        for y in range(7, 18):                                              # a crescent stamped in the face
            for x in range(8, 17):
                if math.hypot(x - 11, y - 12) < 4.5 and math.hypot(x - 13, y - 11) >= 3.8:
                    g[(x, y)] = ("moonc", 3)
        g[(9, 8)] = ("moonc", 0)
        return g
    if name == "health_potion":
        c.blob(12, 15, 6, 5.5, "glass")
        c.poly([(10, 4), (14, 4), (14, 10), (10, 10)], "glass")
        c.poly([(9.5, 3), (14.5, 3), (14.5, 5), (9.5, 5)], "wood")
        g = c.finish()
        for y in range(12, 20):                                             # the rosy draught inside
            for x in range(7, 18):
                if (x, y) in g and g[(x, y)][0] == "glass" and math.hypot(x - 12, y - 15) < 5:
                    g[(x, y)] = ("potion", 0 if (x < 10 and y < 14) else 1 if y < 17 else 2)
        g[(9, 12)] = ("glass", 0)
        return g
    if name == "wood":
        for k, (y, x0) in enumerate(((15, 4), (10, 6), (6, 8))):
            c.poly([(x0, y), (x0 + 13, y - 1), (x0 + 13, y + 4), (x0, y + 5)], "wood")
        g = c.finish()
        for k, (y, x0) in enumerate(((15, 4), (10, 6), (6, 8))):            # cut ends with rings
            for dy in range(1, 4):
                g[(x0 + 12, y + dy)] = ("bone", 1 if dy == 2 else 2)
        return g
    if name == "glowcap":
        c.poly([(10, 12), (14, 12), (14.5, 21), (9.5, 21)], "stem")
        c.poly([(3, 13), (6, 6), (12, 3), (18, 6), (21, 13)], "cap")
        g = c.finish()
        for x, y in ((8, 7), (14, 6), (16, 10), (6, 11), (11, 9)):
            g[(x, y)] = ("cap", 0)
        return g
    if name == "dye_glow":
        c.poly([(6, 10), (18, 10), (20, 20), (4, 20)], "pouch")
        c.poly([(8, 6), (16, 6), (18, 10), (6, 10)], "pouch", dark=1)
        g = c.finish()
        for x in range(7, 18):                                              # drawstring
            g[(x, 10)] = ("bone", 1)
        for (x, y) in ((9, 14), (12, 13), (15, 15), (11, 17), (14, 18)):    # glowing dye dots (the glow finish)
            g[(x, y)] = ("cap", 0)
        for (x, y) in ((12, 3), (8, 4), (16, 4)):
            g[(x, y)] = ("cap", 1)
        return g
    if name == "coin":
        c.blob(12, 12, 7, 7, "gold")
        g = c.finish()
        for y in range(8, 17):                                              # a stamped paw print
            pass
        for (x, y) in ((11, 13), (12, 13), (13, 13), (11, 14), (12, 14), (13, 14), (9, 10), (12, 9), (15, 10)):
            g[(x, y)] = ("gold", 2)
        g[(9, 8)] = ("gold", 0)
        return g
    raise KeyError(name)


LOOK_ICONS = [("obsidian_greatsword", "epic", "weapon"), ("leather_vest", "common", "icon"), ("moon_coin", "rare", "icon"),
              ("health_potion", "common", "icon"), ("wood", "common", "icon"), ("glowcap", "common", "icon"),
              ("dye_glow", "rare", "icon"), ("coin", "common", "icon")]


if __name__ == "__main__":
    write("frames", [frame(k) for k in ("common", "rare", "epic")], {"frame_names": ["common", "rare", "epic"],
                                                                       "icon_window": [3, 3, 18, 18], "glow": "epic"})
    if LOOK:
        imgs = [weapon_icon(n) if kind == "weapon" else icon(n) for n, _, kind in LOOK_ICONS]
        write("icons_look", imgs, {"icon_names": [n for n, _, _ in LOOK_ICONS], "rarity": [r for _, r, _ in LOOK_ICONS]})
