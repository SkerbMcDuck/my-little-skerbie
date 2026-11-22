# Builds the home den's atmosphere (ART_BRIEF §6):
#   - 4 skies (dawn, day, dusk, night), 225x146, drawn behind the den background, which is
#     transparent above the treeline. Gradients step through palette colours with an ordered
#     (Bayer) dither in the transitions, so there's no smear and no hard banding.
#   - 4 lighting overlays per phase, 225x487 RGBA PNGs (soft glow layers may be semi-
#     transparent): tint_<phase>.png (a colour wash, strong on the surface, light in the den)
#     and glow_<phase>.png (warm pools of light around the hearth and lantern spots, brightest
#     at night). The game draws tint over the scene, then glow additively. lighting.json
#     lists the same values for code-side tinting.
#   - Ambient sprites: rain (225x146 loop [4]), door drips (12x16 [3]), a drifting leaf
#     (8x8 tumble [4]; the game moves it), fireflies (7x7 blink [4]), mist wisp (64x14 [4]).
# Usage: python tools/build_atmosphere.py
#        then render art/source/home/sky.json and art/source/home/ambient.json with tools/render.py
import json, math, os, random
from PIL import Image

W, SKY_H, H = 225, 146, 487
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
os.makedirs("art/source/home", exist_ok=True)
os.makedirs("art/out/home/lighting", exist_ok=True)

# ---- Skies ----
SKY_PAL = {
    "a": "#17151c", "b": "#2a2036", "c": "#3a2d4a", "d": "#4a3a5c",           # deep night to dusky purple
    "e": "#2a3448", "f": "#3b4a63", "g": "#4d5e7a",                           # slate blues
    "h": "#615b6b", "i": "#8a8494",                                           # overcast greys
    "j": "#f2a0b0", "k": "#ffc8a8", "l": "#ff8a3d", "m": "#ffb35c", "n": "#ffd08a",  # warm
    "s": "#ffffff", "t": "#fff4b0", "u": "#cfe9ff", "v": "#9fc9f0",           # stars, moon
}
SKIES = {  # colour stops from the top of the sky to the horizon
    "dawn":  ["e", "f", "d", "h", "j", "k"],      # cool pinkish-grey, lifting to peach
    "day":   ["f", "g", "h", "h", "i", "i"],      # muted overcast, never bright sunny
    "dusk":  ["b", "c", "d", "j", "l", "m"],      # deep purple down through rose to orange
    "night": ["a", "a", "b", "e", "e", "f"],      # dark blue, a little lighter at the horizon
}


def sky(name):
    stops = SKIES[name]
    rnd = random.Random(name)
    g = [["." for _ in range(W)] for _ in range(SKY_H)]
    for y in range(SKY_H):
        t = y / (SKY_H - 1) * (len(stops) - 1)
        i, f = int(t), t - int(t)
        for x in range(W):
            # Dither only in the middle of each step: a solid band, then a dithered blend.
            blend = max(0, min(1, (f - 0.55) / 0.45))
            g[y][x] = stops[min(i + 1, len(stops) - 1)] if blend * 16 > BAYER[y % 4][x % 4] else stops[i]
    if name in ("day", "dawn"):  # soft cloud banks, two tones, long and low
        for _ in range(7 if name == "day" else 4):
            cx, cy, rx, ry = rnd.randint(0, W), rnd.randint(10, 80), rnd.randint(22, 46), rnd.randint(4, 8)
            for y in range(cy - ry, cy + ry + 1):
                for x in range(cx - rx, cx + rx + 1):
                    if 0 <= x < W and 0 <= y < SKY_H:
                        d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                        if d <= 1:
                            lit = y < cy - ry * 0.2
                            g[y][x] = ("i" if lit else "h") if name == "day" else ("k" if lit else "j")
    if name == "night":  # stars (a few bright ones with a cross) and a small moon
        for _ in range(60):
            x, y = rnd.randrange(W), rnd.randrange(0, 100)
            g[y][x] = rnd.choice("stu")
        for _ in range(5):
            x, y = rnd.randrange(4, W - 4), rnd.randrange(4, 80)
            g[y][x] = "s"
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                g[y + dy][x + dx] = "u"
        mx, my = 170, 26
        for y in range(my - 6, my + 7):
            for x in range(mx - 6, mx + 7):
                d = math.hypot(x - mx, y - my)
                if d <= 6:
                    g[y][x] = "v" if math.hypot(x - mx + 2, y - my + 2) > 5.5 else "u"
    if name == "dawn":  # mist lying low over the treeline
        for y in range(108, SKY_H):
            for x in range(W):
                if BAYER[y % 4][x % 4] < (y - 108) * 0.45:
                    g[y][x] = "i"
    return ["".join(r) for r in g]


json.dump({"width": W, "height": SKY_H, "fps": 1, "palette": SKY_PAL, "dye_zones": {}, "attach": {},
           "animations": {name: [sky(name)] for name in SKIES}}, open("art/source/home/sky.json", "w"))

# ---- Lighting overlays (RGBA PNGs) ----
SURFACE = 146
LIGHT = {  # tint colour, tint alpha on the surface, alpha in the den, glow strength
    "dawn":  {"tint": (242, 160, 176), "surface": 0.16, "den": 0.06, "glow": 0.45},
    "day":   {"tint": (201, 207, 214), "surface": 0.08, "den": 0.03, "glow": 0.25},
    "dusk":  {"tint": (255, 138, 61), "surface": 0.20, "den": 0.08, "glow": 0.65},
    "night": {"tint": (42, 52, 72), "surface": 0.42, "den": 0.22, "glow": 1.0},
}
GLOWS = {  # warm light sources in the den (ART_BRIEF §6.1). The game draws a source's glow only
           # when that light exists: the Burrow's candle is "wall_left"; lanterns and the hearth
           # light up as they're built.
    "hearth": (124, 350, 62, (255, 179, 92)),       # the fire, just above the hearth spot
    "wall_left": (34, 292, 34, (255, 208, 138)),    # left decor spot (and the Burrow's candle)
    "wall_right": (204, 254, 30, (255, 208, 138)),  # right decor spot
    "door": (115, 124, 22, (255, 200, 140)),
}
for phase, L in LIGHT.items():
    tint = Image.new("RGBA", (W, H))
    for y in range(H):
        a = L["surface"] if y < SURFACE else L["den"] + (L["surface"] - L["den"]) * max(0, (SURFACE + 20 - y) / 20)
        for x in range(W):
            tint.putpixel((x, y), L["tint"] + (int(255 * a),))
    tint.save(f"art/out/home/lighting/tint_{phase}.png")
    for src, (gx, gy, r, col) in GLOWS.items():
        # One small sprite per light, centred on its spot (2r x 2r), drawn additively.
        glow = Image.new("RGBA", (2 * r, 2 * r))
        for y in range(2 * r):
            for x in range(2 * r):
                d = math.hypot(x + .5 - r, y + .5 - r) / r
                if d < 1:
                    # Step the falloff into 8 rings: crisp like pixel art, but no hard visible circles.
                    ring = math.ceil((1 - d) * 8) / 8
                    glow.putpixel((x, y), col + (int(255 * 0.55 * L["glow"] * ring * ring),))
        glow.save(f"art/out/home/lighting/glow_{src}_{phase}.png")
for old in [f for f in os.listdir("art/out/home/lighting") if f.startswith("glow_") and f.count("_") == 1]:
    os.remove(os.path.join("art/out/home/lighting", old))   # the earlier all-in-one glow maps
json.dump({"surface_rows": SURFACE, "phases": {p: dict(L, tint=list(L["tint"])) for p, L in LIGHT.items()},
           "glows": {s: {"x": x, "y": y, "radius": r, "colour": list(c)} for s, (x, y, r, c) in GLOWS.items()},
           "hours": {"dawn": [6, 9], "day": [9, 17], "dusk": [17, 20], "night": [20, 6]}},
          open("art/out/home/lighting/lighting.json", "w"), indent=2)

# ---- Ambient sprites ----
AMB_PAL = {"o": "#0f0d14", "r": "#9fc9f0", "R": "#4d5e7a",            # rain
           "w": "#8ff0e6", "W": "#2ec4b6",                             # water drip
           "L": "#ff8a3d", "M": "#c2410c", "N": "#ffb35c", "G": "#557a5c", "H": "#3e5a46",   # leaves
           "Y": "#fff4b0", "Z": "#e4f27a", "y": "#c8e04a",              # firefly
           "m": "#8a8494", "n": "#615b6b"}                              # mist
anim = {}

# Rain: slanted 3 px streaks falling 6 px per frame; seamless over 4 frames (24 px drop cycle).
rnd = random.Random(3)
drops = [(rnd.randrange(W), rnd.randrange(24), rnd.randrange(SKY_H // 24 + 1)) for _ in range(70)]
rain = []
for f in range(4):
    g = {}
    for x0, y0, band in drops:
        for rep in range(SKY_H // 24 + 2):
            y = (y0 + f * 6) % 24 + rep * 24
            x = x0 - (y // 3)
            for k in range(3):
                g[((x - k // 2) % W, y + k)] = "r" if k == 0 else "R"
    rain.append(["".join(g.get((x, y), ".") for x in range(W)) for y in range(SKY_H)])
anim["rain"] = rain

# Door drips: a drop gathers on the lip of the root door, falls and splashes. 12x16.
def drip(stage):
    g = {}
    if stage == 0:
        g.update({(6, 0): "W", (6, 1): "w"})
    elif stage == 1:
        g.update({(6, 0): "W", (6, 6): "w", (6, 7): "W"})
    else:
        g.update({(6, 0): "W", (4, 14): "w", (8, 14): "w", (5, 15): "W", (7, 15): "W", (6, 13): "w"})
    return ["".join(g.get((x, y), ".") for x in range(12)) for y in range(16)]
anim["door_drip"] = [drip(s) for s in range(3)]

# A leaf tumbling as it drifts: 4 turns of an outlined autumn leaf. 8x8.
LEAF = ["...oo...", "..oLLo..", ".oLNLLo.", "oLNLMLo.", ".oLMLLo.", "..oLLo..", "...oMo..", "....o..."]
def turn(rows, k):
    pts = {(x, y): c for y, r in enumerate(rows) for x, c in enumerate(r) if c != "."}
    out = {}
    for (x, y), c in pts.items():
        X, Y = x - 3.5, y - 3.5
        if k == 1:
            X, Y = Y, -X
        elif k == 2:
            X, Y = -X * 0.5, -Y   # edge-on: squashed
        elif k == 3:
            X, Y = -Y, X
        out[(round(X + 3.5), round(Y + 3.5))] = c
    return ["".join(out.get((x, y), ".") for x in range(8)) for y in range(8)]
EDGE_ON = ["...o....", "..oLo...", "..oNo...", "..oLo...", "..oMo...", "..oLo...", "...oo...", "....o..."]
anim["leaf"] = [turn(LEAF, 0), turn(LEAF, 1), EDGE_ON, turn(LEAF, 3)]  # frame 2: seen edge-on

# Fireflies: a tiny bug whose glow swells and fades. 7x7.
def firefly(f):
    g = {(3, 3): "Y"}
    if f in (1, 2):
        g.update({(2, 3): "Z", (4, 3): "Z", (3, 2): "Z", (3, 4): "Z"})
    if f == 2:
        g.update({(1, 3): "y", (5, 3): "y", (3, 1): "y", (3, 5): "y", (2, 2): "y", (4, 4): "y", (2, 4): "y", (4, 2): "y"})
    if f == 3:
        g = {(3, 3): "Z"}
    return ["".join(g.get((x, y), ".") for x in range(7)) for y in range(7)]
anim["firefly"] = [firefly(f) for f in range(4)]

# Mist wisp: a long, soft dithered band that breathes. 64x14.
def mist(f):
    g = {}
    for y in range(14):
        for x in range(64):
            body = math.sin(x / 64 * math.pi) * (1 - abs(y - 7) / 7)
            wave = 0.15 * math.sin(x / 7 + f * math.pi / 2)
            v = body + wave
            if v * 16 > BAYER[y % 4][x % 4] + 4:
                g[(x, y)] = "m" if v > 0.6 else "n"
    return ["".join(g.get((x, y), ".") for x in range(64)) for y in range(14)]
anim["mist"] = [mist(f) for f in range(4)]

# Different sizes per animation, so each is its own JSON (render.py expects one size per file).
for name, frames in anim.items():
    w, h = len(frames[0][0]), len(frames[0])
    json.dump({"width": w, "height": h, "fps": 8, "palette": AMB_PAL, "dye_zones": {}, "attach": {},
               "animations": {name: frames}}, open(f"art/source/home/ambient_{name}.json", "w"))
print("skies, lighting overlays and ambient sprites written")
