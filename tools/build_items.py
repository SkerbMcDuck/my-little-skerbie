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
    "leaf":   ["#557a5c", "#3e5a46", "#2c4234", "#1f3d44"],
    "rust":   ["#a8643a", "#7a5636", "#3b2a22", "#17151c"],
    "siron":  ["#5a5e66", "#33303d", "#23212b", "#17151c"],            # shadow iron
    "fire":   ["#ffe08a", "#ffb347", "#ff7a1a", "#c2410c"],
    "stone":  ["#8a8494", "#615b6b", "#433e4c", "#23212b"],
    "bomb":   ["#5a5e66", "#33303d", "#23212b", "#17151c"],
    "smokeg": ["#8a8494", "#615b6b", "#433e4c", "#2c2833"],
    "meat":   ["#ffc8a8", "#a8643a", "#7a5636", "#3b2a22"],
    "berryb": ["#cfe9ff", "#9fc9f0", "#4d5e7a", "#2a3448"],            # moonberry
    "mint":   ["#cfe9ff", "#8ff0e6", "#2ec4b6", "#178f86"],            # frostmint
    "root":   ["#8a8494", "#615b6b", "#433e4c", "#3b2a22"],            # ironroot
    "plum":   ["#e2b8ff", "#4a3a5c", "#3a2d4a", "#2a2036"],            # shadow plum: dusky, a pale bloom
    "soil":   ["#4a3a5c", "#3a2d4a", "#2a2036", "#17151c"],
    "fox":    ["#ffb35c", "#ff8a3d", "#a8643a", "#3b2a22"],
    "foxw":   ["#ffc8a8", "#bfae8c", "#a8945e", "#8b7a4a"],
    "cloak":  ["#4a3a5c", "#3a2d4a", "#2a2036", "#17151c"],
    "teal":   ["#8ff0e6", "#2ec4b6", "#178f86", "#1f3d44"],
    "pink":   ["#ffc8a8", "#f2a0b0", "#4a3a5c", "#2a2036"],
    "lamp":   ["#ffe08a", "#ffd08a", "#ffb35c", "#ff8a3d"],
    "sack":   ["#bfae8c", "#a8945e", "#8b7a4a", "#5f7a3a"],
    "beye":   ["#ffd08a", "#ffb35c", "#ffb35c", "#ffb35c"],
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



def icon2(name):
    # The rest of the icons.
    c = Canvas(24, 24)
    g = None
    if name == "leaf_wrap":
        for (x, y, r) in ((9, 9, 4), (15, 9, 4), (8, 14, 4.2), (16, 14, 4.2), (12, 18, 4.5), (12, 11, 3.5)):
            c.blob(x, y, r, r * 0.8, "leaf")
        g = c.finish()
        for y in range(7, 21):
            g[(12, y)] = ("leaf", 3)
    elif name == "scrap_plate":
        c.poly([(6, 6), (18, 6), (19, 18), (12, 20), (5, 18)], "iron")
        c.poly([(13, 8), (18, 9), (17, 15), (13, 14)], "rust")
        g = c.finish()
        for p in ((7, 8), (16, 7), (7, 16), (17, 17), (12, 18)):
            g[p] = ("iron", 0)
    elif name == "chain_cowl":
        c.poly([(7, 18), (6, 9), (9, 4), (15, 4), (18, 9), (17, 18), (14, 20), (10, 20)], "iron")
        c.poly([(9, 9), (15, 9), (14, 16), (10, 16)], "siron", dark=2)
        g = c.finish()
        for y in range(5, 20, 2):
            for x in range(7, 18, 2):
                if g.get((x, y), ("o",))[0] == "iron":
                    g[(x + (y // 2) % 2, y)] = ("iron", 2)
    elif name == "bone_armor":
        c.poly([(7, 5), (17, 5), (18, 19), (6, 19)], "leath", dark=1)
        g_ = None
        for y in (7, 10, 13, 16):
            c.poly([(6, y), (18, y), (17, y + 2), (7, y + 2)], "bone")
        c.poly([(11, 5), (13, 5), (13, 19), (11, 19)], "bone")
        g = c.finish()
    elif name == "shadow_iron_plate":
        c.poly([(6, 6), (10, 4), (12, 6), (14, 4), (18, 6), (19, 18), (12, 21), (5, 18)], "siron")
        g = c.finish()
        for (x, y) in ((8, 7), (9, 8), (16, 7), (15, 8), (12, 12), (12, 13)):
            g[(x, y)] = ("iron", 0)
        for y in range(8, 19):
            g[(12, y)] = ("mind", 3)
    elif name == "fang":
        for t in range(13):                                                 # a cord looped round the fang's root
            a = math.radians(200 + t * 11)
            c.px(12 + 8 * math.cos(a), 9 + 6 * math.sin(a), "leath", 1)
        c.poly([(8, 6), (16, 6), (16, 9), (14, 15), (10, 21), (9, 13)], "bone")
        c.poly([(7, 5), (17, 5), (17, 7), (7, 7)], "leath")
        g = c.finish()
        g[(10, 9)] = ("bone", 0)
        g[(10, 10)] = ("bone", 0)
    elif name == "feather":
        c.poly([(17, 3), (20, 6), (11, 17), (6, 20), (8, 13)], "pink")
        c.stick((5, 21), (18, 5), 1.4, 1.4, "stem")
        g = c.finish()
        for t in range(1, 6):
            g[(8 + t * 2, 16 - t * 2)] = ("pink", 2)
    elif name == "eye_stone":
        c.blob(12, 12, 7.5, 6.5, "stone")
        g = c.finish()
        for x in range(7, 18):                                              # a carved eye glowing Mind purple
            dy = int(2.5 * math.sin(math.pi * (x - 7) / 10))
            g[(x, 12 - dy)] = ("mind", 1)
            g[(x, 12 + dy)] = ("mind", 1)
        for p in ((12, 12), (11, 12), (12, 11), (13, 12), (12, 13)):
            g[p] = ("mind", 0)
    elif name == "bone_die":
        c.poly([(6, 9), (12, 6), (18, 9), (18, 16), (12, 20), (6, 16)], "bone")
        g = c.finish()
        for p in ((12, 9), (9, 13), (10, 16), (15, 12), (16, 15), (14, 14)):
            g[p] = ("bone", 3)
        for y in range(10, 20):
            g[(12, y)] = ("bone", 2)
    elif name == "ember_shard":
        c.poly([(12, 2), (17, 9), (14, 21), (9, 21), (7, 9)], "fire")
        g = c.finish()
        for p in ((11, 6), (10, 9), (12, 13)):
            g[p] = ("fire", 0)
    elif name == "power_tonic":
        c.poly([(9, 8), (15, 8), (18, 20), (6, 20)], "glass")
        c.poly([(10, 3), (14, 3), (14, 8), (10, 8)], "glass")
        c.poly([(9.5, 2), (14.5, 2), (14.5, 4), (9.5, 4)], "rust")
        g = c.finish()
        for y in range(12, 20):
            for x in range(7, 18):
                if g.get((x, y), ("o",))[0] == "glass":
                    g[(x, y)] = ("tonic", 0 if y < 14 and x < 11 else 1 if y < 17 else 2)
    elif name == "bomb":
        c.blob(11, 14, 7, 7, "bomb")
        c.poly([(12, 5), (16, 5), (16, 8), (12, 8)], "iron")
        g = c.finish()
        for p in ((15, 4), (16, 3), (17, 3)):
            g[p] = ("leath", 1)
        for p in ((18, 2), (19, 1), (19, 3), (18, 1)):
            g[p] = ("fire", 0)
        g[(8, 11)] = ("bomb", 0)
    elif name == "smoke_bomb":
        c.blob(12, 15, 6.5, 6, "smokeg")
        c.stick((12, 9), (12, 6), 2.6, 2.6, "leath")
        g = c.finish()
        for (x, y) in ((10, 4), (13, 3), (15, 5), (9, 2), (14, 1)):
            g[(x, y)] = ("smokeg", 1)
        g[(10, 12)] = ("smokeg", 0)
    elif name == "snack":
        c.stick((13, 13), (19, 19), 3.2, 3.2, "bone")                       # a meaty drumstick
        c.blob(19, 20, 2.2, 2.2, "bone")
        c.blob(20.5, 18.5, 2.2, 2.2, "bone")
        c.poly([(4, 9), (8, 4), (14, 5), (17, 11), (14, 16), (7, 16)], "meat")
        g = c.finish()
        for p_ in ((8, 7), (9, 6), (7, 8)):
            g[p_] = ("meat", 0)
    elif name == "stone":
        for (x, y, r) in ((9, 15, 5.5), (15, 14, 4.5), (12, 9, 4.5)):
            c.blob(x, y, r, r * 0.85, "stone")
        g = c.finish()
    elif name == "scrap":
        c.poly([(4, 16), (13, 13), (15, 19), (5, 20)], "iron")
        c.blob(15, 9, 5, 5, "rust")
        g = c.finish()
        for k in range(8):                                                  # a gear's teeth
            a = math.radians(k * 45)
            g[(int(15 + 6 * math.cos(a)), int(9 + 6 * math.sin(a)))] = ("rust", 1)
        g[(15, 9)] = ("o",)
    elif name == "ember_pepper":
        c.poly([(9, 6), (16, 6), (18, 11), (15, 17), (8, 21), (6, 19), (10, 14), (8, 9)], "fire")
        c.poly([(10, 4), (15, 4), (15, 7), (10, 7)], "leaf")
        c.stick((13, 4), (16, 1), 2, 1.6, "leaf")
        g = c.finish()
        for p_ in ((10, 8), (11, 9), (11, 10)):
            g[p_] = ("fire", 0)
    elif name == "moonberry":
        c.stick((12, 4), (12, 9), 1.4, 1.4, "leaf")
        c.poly([(12, 5), (18, 3), (15, 7)], "leaf")
        g = c.finish()
        for p_ in ((8, 12), (16, 12), (12, 18)):                             # three plump round berries, each outlined
            bx, by = p_
            for dy in range(-5, 6):                                         # a round pixel disc with its own outline
                for dx in range(-5, 6):
                    d2 = dx * dx + dy * dy
                    if d2 <= 13:
                        lit = -dx - dy
                        g[(bx + dx, by + dy)] = ("berryb", 0 if lit >= 4 else 1 if lit >= -1 else 2)
                    elif d2 <= 22:
                        g[(bx + dx, by + dy)] = ("o",)
            g[(p_[0] - 2, p_[1] - 2)] = ("berryb", 0)
            g[(p_[0] - 1, p_[1] - 2)] = ("berryb", 0)
            g[(p_[0] + 1, p_[1] + 2)] = ("berryb", 3)
    elif name == "frostmint":
        c.stick((12, 21), (12, 6), 1.6, 1.4, "leaf")
        for (x, y, a) in ((8, 15, 1), (16, 13, -1), (8, 9, 1), (16, 7, -1)):
            c.blob(x, y, 3.6, 2.2, "mint")
        g = c.finish()
        for p in ((7, 14), (15, 12), (7, 8), (15, 6)):
            g[p] = ("mint", 0)
    elif name == "ironroot":
        c.poly([(7, 8), (17, 8), (16, 15), (13, 21), (11, 21), (8, 15)], "root")
        c.stick((9, 16), (5, 20), 1.6, 1, "root")
        c.stick((15, 16), (19, 20), 1.6, 1, "root")
        c.stick((12, 8), (9, 3), 2, 1.4, "leaf")
        c.stick((12, 8), (15, 2), 2, 1.4, "leaf")
        g = c.finish()
        for y in (11, 14, 17):
            g[(11, y)] = ("root", 3)
            g[(13, y - 1)] = ("root", 3)
    elif name == "shadow_plum":
        c.blob(12, 13, 7, 6.5, "plum")
        c.stick((12, 7), (13, 3), 1.6, 1.4, "leath")
        c.poly([(13, 4), (18, 3), (16, 6)], "leaf")
        g = c.finish()
        for p in ((9, 10), (8, 11), (9, 11)):
            g[p] = ("plum", 0)
        for y in range(8, 19):
            if (12, y) in g:
                g[(12, y)] = ("plum", 3)
    elif name == "coin_stack":
        for k in range(5):                                                  # coins stacked edge-on, the top one face-up
            c.blob(11, 19 - k * 3, 6.5, 2.4, "gold", dark=(1 if k < 4 else 0))
        c.blob(18, 18, 3.2, 3.6, "gold")                                     # one more leaning against the stack
        g = c.finish()
        for x in range(7, 15):
            g[(x, 7)] = ("gold", 0)
        g[(17, 16)] = ("gold", 0)
    elif name.startswith("dye_"):
        finish = name[4:]
        c.poly([(6, 10), (18, 10), (20, 20), (4, 20)], "pouch")
        c.poly([(8, 6), (16, 6), (18, 10), (6, 10)], "pouch", dark=1)
        g = c.finish()
        for x in range(7, 18):
            g[(x, 10)] = ("bone", 1)
        if finish == "metallic":
            for t in range(6):
                g[(8 + t, 18 - t)] = ("silver", 0 if t % 2 else 1)
                g[(11 + t, 19 - t)] = ("silver", 1)
        elif finish == "two_tone":
            for y in range(11, 20):
                for x in range(5, 20):
                    if (x, y) in g and g[(x, y)][0] == "pouch" and x > 12:
                        g[(x, y)] = ("teal", 1 if y < 15 else 2)
        elif finish == "sparkle":
            for (x, y) in ((9, 14), (15, 13), (12, 17)):
                g[(x, y)] = ("gold", 0)
                for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    g[(x + d[0], y + d[1])] = ("gold", 1)
        elif finish == "smoke":
            for (x, y) in ((10, 4), (13, 3), (15, 5), (11, 1), (14, 0)):
                g[(x, y)] = ("smokeg", 1)
            for (x, y) in ((9, 14), (14, 15), (11, 17)):
                g[(x, y)] = ("smokeg", 0)
    if g is None:
        return icon(name)
    return g


GROUPS = {
    "weapons":     [("bone_club", "common"), ("twin_knives", "common"), ("spear", "rare"), ("hooked_blade", "rare"),
                    ("rune_staff", "epic"), ("obsidian_greatsword", "epic")],
    "armors":      [("leaf_wrap", "common"), ("leather_vest", "common"), ("scrap_plate", "rare"), ("chain_cowl", "rare"),
                    ("bone_armor", "epic"), ("shadow_iron_plate", "epic")],
    "charms":      [("fang", "common"), ("feather", "common"), ("bone_die", "rare"), ("moon_coin", "rare"),
                    ("eye_stone", "epic"), ("ember_shard", "epic")],
    "consumables": [("health_potion", "common"), ("power_tonic", "common"), ("bomb", "common"), ("smoke_bomb", "common"),
                    ("snack", "common")],
    "materials":   [("wood", "common"), ("stone", "common"), ("scrap", "common")],
    "ingredients": [("glowcap", "common"), ("ember_pepper", "common"), ("moonberry", "common"), ("frostmint", "common"),
                    ("ironroot", "common"), ("shadow_plum", "common")],
    "dyes":        [("dye_metallic", "rare"), ("dye_glow", "rare"), ("dye_two_tone", "rare"), ("dye_sparkle", "rare"),
                    ("dye_smoke", "epic")],
    "currency":    [("coin", "common"), ("coin_stack", "common")],
}


# ============================================================================ garden plants
def plant(crop, stage):
    # 20x24, anchor bottom-centre on a garden slot. stage 0 sprout, 1 growing, 2 ripe (with a soft sparkle).
    c = Canvas(20, 24)
    G = 23
    c.blob(10, G - 1, 7, 2.2, "soil")                                       # the mound it grows from
    h = (6, 12, 17)[stage]
    if crop == "glowcap":
        caps = [(10, G - 4, 2.4)] if stage == 0 else [(8, G - 6, 3), (13, G - 8, 3.5)] if stage == 1 else \
            [(6, G - 6, 3), (11, G - 11, 4.5), (15, G - 6, 3.2)]
        for (x, y, r) in caps:
            c.stick((x, G - 2), (x, y + 1), 1.8, 1.6, "stem")
            c.blob(x, y, r, r * 0.65, "cap")
    elif crop in ("ember_pepper", "moonberry", "shadow_plum"):
        c.stick((10, G - 2), (10, G - h), 2, 1.4, "leaf")
        leaves = [(-3, 0.6), (3, 0.8)] if stage == 0 else [(-4, 0.4), (4, 0.55), (-3, 0.8), (3, 0.95)]
        for dx, t in leaves:
            c.blob(10 + dx, G - h * t, 2.8, 1.8, "leaf")
        if stage == 2:
            fruit = {"ember_pepper": "fire", "moonberry": "berryb", "shadow_plum": "plum"}[crop]
            for (x, y) in ((6, G - 9), (14, G - 11), (10, G - 15), (13, G - 6)):
                if crop == "ember_pepper":
                    c.poly([(x - 1, y - 2), (x + 1.5, y - 2), (x, y + 3)], fruit)
                else:
                    c.blob(x, y, 2.2 if crop == "moonberry" else 2.8, 2.2 if crop == "moonberry" else 2.8, fruit)
        elif stage == 1:
            for (x, y) in ((7, G - 8), (13, G - 10)):
                c.px(x, y, "bone", 1)                                       # flower buds
    elif crop == "frostmint":
        for k in range(1 + stage * 2):
            x = 10 + (k - stage) * 3
            c.stick((x, G - 2), (x, G - h + abs(k - stage) * 3), 1.6, 1.2, "leaf")
            c.blob(x + (1 if k % 2 else -1), G - h + abs(k - stage) * 3, 2.6, 1.7, "mint")
    elif crop == "ironroot":
        if stage >= 1:
            c.poly([(7, G - 3), (13, G - 3), (12, G + 1), (8, G + 1)], "root")   # the root crown shows above the soil
        for k, a in enumerate((-60, -90, -120)[:1 + stage]):
            tip = (10 + h * 0.6 * math.cos(math.radians(a)), G - 3 + h * 0.9 * math.sin(math.radians(a)))
            c.stick((10, G - 3), tip, 2.2, 1.2, "leaf")
            c.blob(tip[0], tip[1], 2.4, 1.6, "leaf")
    g = c.finish()
    if stage == 2:                                                          # the ripe sparkle
        for (x, y) in ((3, 6), (17, 4), (15, 13)):
            g[(x, y)] = ("lamp", 0)
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            g[(17 + d[0], 4 + d[1])] = ("lamp", 2)
    if crop == "glowcap":
        for (x, y), t in list(g.items()):
            if t == ("cap", 0):
                g[(x, y)] = ("teal", 0)
    return g


# ============================================================================ the overflow pile
def pile(size):
    W_, H_ = {"small": (32, 20), "medium": (44, 28), "heaped": (60, 38)}[size]
    c = Canvas(W_, H_)
    G = H_ - 1
    items = {"small": [("sack", 10, 6), ("crate", 22, 5)],
             "medium": [("crate", 10, 8), ("sack", 24, 7), ("crate", 34, 6), ("bundle", 18, 4)],
             "heaped": [("crate", 10, 9), ("sack", 26, 9), ("crate", 44, 8), ("crate", 20, 6), ("sack", 36, 6),
                        ("bundle", 28, 3), ("pot", 50, 5)]}[size]
    for kind, x, r in items:
        lift = (H_ - 4 - r * 2) if r < 7 and size != "small" else 0
        base = G - (0 if r >= 7 else max(0, H_ * 0.45 - r))
        if kind == "crate":
            c.poly([(x - r, base - r * 1.6), (x + r, base - r * 1.6), (x + r, base), (x - r, base)], "wood")
        elif kind == "sack":
            c.blob(x, base - r * 0.9, r, r * 0.9, "sack")
            c.stick((x - 1, base - r * 1.8), (x + 1, base - r * 2.2), 2, 1.4, "sack")
        elif kind == "bundle":
            c.stick((x - 8, base - 3), (x + 8, base - 6), 3, 3, "wood")
            c.stick((x - 7, base - 6), (x + 9, base - 3), 3, 3, "wood")
        elif kind == "pot":
            c.blob(x, base - r, r, r, "rust")
    g = c.finish()
    for (x, y), t in list(g.items()):                                       # plank seams on the crates
        if t[0] == "wood" and x % 5 == 0:
            g[(x, y)] = ("wood", 3)
    return g


# ============================================================================ the merchant fox and his cart
def merchant(anim, f):
    W_, H_ = 112, 64
    c = Canvas(W_, H_)
    G = H_ - 1
    walk = anim == "arrive"
    bob = (0, -1, 0, -1)[f % 4] if walk else (0, -1, 0)[f % 3]
    sway = (math.sin(f * 1.6) * 2) if walk else math.sin(f * 2.1)
    # the cart: a rickety box on two big wheels under a patched canopy hung with lanterns and trinkets
    wx, wy, wr = 30, G - 9, 9
    c.poly([(2, 24), (62, 24), (60, 27), (4, 27)], "wood", dark=1)           # the rim (goods go behind its front)
    c.poly([(4, 8), (60, 8), (64, 16), (0, 16)], "cloak")                    # canopy
    for x in (6, 58):
        c.stick((x, 16), (x, 26), 2.4, 2.4, "wood")
    for k, (x, y, kind) in enumerate(((12, 26, "bottle"), (20, 27, "pot"), (28, 26, "bottle"), (37, 27, "crate"),
                                      (46, 26, "bottle"), (53, 27, "pot"))):  # goods poking up out of the box
        if kind == "bottle":
            c.poly([(x - 2.5, y - 8), (x + 2.5, y - 8), (x + 2.5, y), (x - 2.5, y)], "teal" if k % 2 else "pink")
            c.poly([(x - 1, y - 11), (x + 1, y - 11), (x + 1, y - 8), (x - 1, y - 8)], "teal" if k % 2 else "pink")
        elif kind == "pot":
            c.blob(x, y - 4, 4, 3.6, "rust")
        else:
            c.poly([(x - 4.5, y - 8), (x + 4.5, y - 8), (x + 4.5, y), (x - 4.5, y)], "wood", dark=1)
    c.poly([(6, 26), (58, 26), (60, 46), (4, 46)], "wood")                   # the box front
    c.blob(wx, wy, wr, wr, "wood", dark=1)                                  # the wheel
    c.blob(wx, wy, wr - 2.5, wr - 2.5, "wood", dark=2)
    c.stick((60, 40), (82, 38 + bob), 2.6, 2.6, "wood")                      # the shafts he pulls by
    g = c.finish()
    spin = f * 22 if walk else 0
    for k in range(6):                                                      # wheel spokes, turning as he walks
        a = math.radians(k * 60 + spin)
        for t in range(1, int(wr - 1)):
            g[(int(round(wx + t * math.cos(a))), int(round(wy + t * math.sin(a))))] = ("wood", 1)
    g[(wx, wy)] = ("iron", 1)
    for k, x in enumerate((10, 24, 40, 54)):                                # lanterns swinging from the canopy
        sw = int(round(sway * (1 if k % 2 else -1)))
        for y in range(16, 19):
            g[(x, y)] = ("iron", 2)
        for y in range(19, 24):
            for dx in (-1, 0, 1):
                g[(x + dx + sw, y)] = ("lamp", 0 if dx == 0 and y in (20, 21) else 2)
        g[(x + sw, 24)] = ("iron", 2)
    for x in range(2, 62, 6):                                               # canopy patches and fringe
        g[(x, 16)] = ("cloak", 3)
        g[(x + 2, 17)] = ("cloak", 2)
    for (x, y) in ((18, 12), (44, 10)):
        g[(x, y)] = ("sack", 1)
        g[(x + 1, y)] = ("sack", 1)
    # the fox: hunched in a cloak, hood fallen back, leaning into the shafts; a big bushy white-tipped tail
    c2 = Canvas(W_, H_)
    lean = 2 if walk else 0
    fx0 = 90 + lean
    for k, (dx, ph) in enumerate(((-3, 0), (3, 2))):                        # legs
        off = (2 if ((f + ph) % 4) < 2 else -2) if walk else 0
        c2.stick((fx0 + dx, G - 12 + bob), (fx0 + dx + off, G - 2), 3.4, 3, "fox", dark=1 if k == 0 else 0)
        c2.poly([(fx0 + dx + off - 2, G - 2), (fx0 + dx + off + 3, G - 2), (fx0 + dx + off + 3, G), (fx0 + dx + off - 2, G)], "cloak", dark=2)
    tail_up = (0, 1, 2)[f % 3] if not walk else (0, 1, 0, -1)[f % 4]
    tu = tail_up
    c2.poly([(fx0 - 6, G - 11 + bob), (fx0 - 14, G - 13 + bob), (fx0 - 21, G - 20 + bob - tu), (fx0 - 23, G - 28 + bob - tu),
             (fx0 - 18, G - 33 + bob - tu), (fx0 - 15, G - 26 + bob - tu), (fx0 - 12, G - 19 + bob), (fx0 - 6, G - 17 + bob)], "fox")
    c2.blob(fx0 - 20, G - 31 + bob - tu, 3.4, 3, "foxw")                    # the white tip
    c2.poly([(fx0 - 9, G - 10 + bob), (fx0 + 8, G - 10 + bob), (fx0 + 6 + lean, G - 28 + bob), (fx0 - 5, G - 30 + bob)], "cloak")
    hx, hy = fx0 + 6 + lean, G - 31 + bob
    c2.poly([(hx - 9, hy + 2), (hx - 4, hy - 1), (hx, hy + 5), (hx - 8, hy + 7)], "cloak", dark=1)   # the hood, fallen back
    for k, ex in enumerate((hx - 3, hx + 2)):                                 # tall pointed ears
        c2.poly([(ex - 2.2, hy - 3), (ex + 2.2, hy - 3), (ex, hy - 11)], "fox", dark=k)
    c2.blob(hx, hy, 5, 4.4, "fox")                                           # the head
    c2.poly([(hx + 2, hy - 2), (hx + 11, hy + 1), (hx + 10, hy + 3), (hx + 2, hy + 4)], "fox")    # the snout
    c2.poly([(hx - 1, hy + 1), (hx + 10, hy + 2.5), (hx + 8, hy + 4.5), (hx - 1, hy + 4.5)], "foxw")   # white cheek and jaw
    c2.stick((fx0 + 2, G - 24 + bob), (82, 38 + bob), 3.4, 3, "cloak")       # arm to the shaft
    c2.blob(82, 38 + bob, 2.6, 2.4, "fox")
    g2 = c2.finish()
    g.update(g2)
    for k, ex in enumerate((hx - 3, hx + 2)):                                 # dark inner ears
        g[(int(ex), int(hy - 7))] = ("fox", 3)
        g[(int(ex), int(hy - 6))] = ("fox", 3)
    g[(int(hx + 3), int(hy - 1))] = ("beye", 0)                              # a sly amber eye
    g[(int(hx + 2), int(hy - 2))] = ("o",)
    g[(int(hx + 3), int(hy - 2))] = ("o",)
    g[(int(hx + 11), int(hy + 1))] = ("o",)                                  # nose
    return g


def write_sprite(name, w, h, anims, anchor):
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
    grids = {a: [["".join(inv[fr[(x, y)]] if (x, y) in fr else "." for x in range(w)) for y in range(h)] for fr in frames]
             for a, frames in anims.items()}
    json.dump({"width": w, "height": h, "fps": 8, "palette": pal, "dye_zones": {}, "attach": {}, "anchor": anchor,
               "animations": grids}, open(f"{OUT}/{name}.json", "w"))
    print("wrote", name)


LOOK_ICONS = [("obsidian_greatsword", "epic", "weapon"), ("leather_vest", "common", "icon"), ("moon_coin", "rare", "icon"),
              ("health_potion", "common", "icon"), ("wood", "common", "icon"), ("glowcap", "common", "icon"),
              ("dye_glow", "rare", "icon"), ("coin", "common", "icon")]


if __name__ == "__main__":
    write("frames", [frame(k) for k in ("common", "rare", "epic")], {"frame_names": ["common", "rare", "epic"],
                                                                       "icon_window": [3, 3, 18, 18], "glow": "epic"})
    if LOOK:
        imgs = [weapon_icon(n) if kind == "weapon" else icon(n) for n, _, kind in LOOK_ICONS]
        write("icons_look", imgs, {"icon_names": [n for n, _, _ in LOOK_ICONS], "rarity": [r for _, r, _ in LOOK_ICONS]})
    else:
        for grp, items in GROUPS.items():
            imgs = [weapon_icon(n) if grp == "weapons" else icon2(n) for n, _ in items]
            write(f"icons_{grp}", imgs, {"icon_names": [n for n, _ in items], "rarity": [r for _, r in items]})
        crops = ["glowcap", "ember_pepper", "moonberry", "frostmint", "ironroot", "shadow_plum"]
        write_sprite("garden_plants", 20, 24, {cr: [plant(cr, st) for st in range(3)] for cr in crops}, [10, 23])
        for sz in ("small", "medium", "heaped"):
            w_, h_ = {"small": (32, 20), "medium": (44, 28), "heaped": (60, 38)}[sz]
            write_sprite(f"overflow_{sz}", w_, h_, {"pile": [pile(sz)]}, [w_ // 2, h_ - 1])
        write_sprite("merchant", 112, 64, {"arrive": [merchant("arrive", f) for f in range(4)],
                                          "idle": [merchant("idle", f) for f in range(3)]}, [56, 63])
