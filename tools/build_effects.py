# Builds the shared effects library (ART_BRIEF §12).
# Usage: python tools/build_effects.py [group ...]      groups: element, mind, general (more after the look test)
#        then: python tools/build_effects.py --render   (renders every JSON and writes its glow layer)
#
# Effects are separate sprites, never baked into bodies. Combat and element effects come in two
# sizes: "small" (for babies, kids and small enemies) and "large" (adults, the Hollow, bosses);
# UI-ish effects come in one size. Each JSON has an "anchor" (the pixel that goes on the hit point,
# or the ground point for ground effects). Glowing effects (fire, lightning, magic) also get a
# soft-glow layer, glow.png next to the sheet: a blurred, brightened copy the game adds on top
# with additive blending ("glow": true in the JSON).
# Style: crisp pixel particles with a bright core and darker edges, no outlines (effects light up
# the scene rather than sit in it). Colours are the element ramps from §3.
import json, math, os, random, sys, zlib

OUT = "art/source/effects/library"
RAMPS = {  # highlight -> deep
    "fire":      ["#ffe08a", "#ffb347", "#ff7a1a", "#c2410c"],
    "water":     ["#8ff0e6", "#2ec4b6", "#178f86", "#1f3d44"],
    "lightning": ["#ffffff", "#fff4b0", "#ffe14d", "#a8945e"],
    "earth":     ["#a8945e", "#8b7a4a", "#5f7a3a", "#3b2a22"],
    "ice":       ["#f2f9ff", "#cfe9ff", "#9fc9f0", "#4d5e7a"],
    "mind":      ["#e2b8ff", "#c77dff", "#9b4dff", "#6a2cc9"],
    "spark":     ["#ffffff", "#ffd08a", "#ffb35c", "#ff8a3d"],
    "gold":      ["#ffe08a", "#f2c14e", "#a8643a", "#3b2a22"],
    "dust":      ["#bfae8c", "#a8945e", "#8b7a4a", "#5f7a3a"],
    "bronze":    ["#ffd08a", "#a8643a", "#7a5636", "#3b2a22"],               # Strength type colour
    "silver":    ["#ffffff", "#c9cfd6", "#8a8494", "#5a5e66"],               # Speed type colour
    "smoke":     ["#7a7088", "#554c63", "#3a3346", "#251f2e"],               # Skerbie's smoke dye zone (s S t T)
    "heal":      ["#ffffff", "#8ff0e6", "#2ec4b6", "#178f86"],
    "white":     ["#ffffff", "#f2f9ff", "#cfe9ff", "#9fc9f0"],
    "cloth":     ["#ffffff", "#bfae8c", "#a8945e", "#8b7a4a"],
}
SMOKE_CHARS = dict(zip(RAMPS["smoke"], "sStT"))
GLOWING = {"fire", "lightning", "mind", "spark", "gold"}
ELEMENTS = ("fire", "water", "lightning", "earth", "ice")
SIZES = {"small": 1, "large": 2}


def hsh(*a):
    # Stable pseudo-random number for a key (Python's hash() changes between runs, so use crc32).
    return random.Random(zlib.crc32(repr(a).encode())).random()


class FX:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = {}

    def dot(self, x, y, col):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[(x, y)] = col

    def blob(self, cx, cy, r, ramp, core=0.45):
        # A round particle: bright core, base, then a darker rim.
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                d = math.hypot(x + .5 - cx, y + .5 - cy) / max(r, .5)
                if d <= 1:
                    self.dot(x, y, ramp[0] if d < core else ramp[1] if d < 0.75 else ramp[2])

    def streak(self, x0, y0, x1, y1, ramp, w=1.0):
        # A tapering line, bright at its head (x1, y1).
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) * 1.5))
        for k in range(n + 1):
            t = k / n
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            col = ramp[0] if t > 0.75 else ramp[1] if t > 0.4 else ramp[2]
            r = w * (0.4 + 0.6 * t)
            if r < 0.8:
                self.dot(x, y, col)
            else:
                for dy in range(-int(r), int(r) + 1):
                    for dx in range(-int(r), int(r) + 1):
                        if dx * dx + dy * dy <= r * r:
                            self.dot(x + dx, y + dy, col)

    def tri(self, pts, col):
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            for x in range(int(min(xs)), int(max(xs)) + 1):
                (x1, y1), (x2, y2), (x3, y3) = pts
                d = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
                if d == 0:
                    continue
                a = ((y2 - y3) * (x + .5 - x3) + (x3 - x2) * (y + .5 - y3)) / d
                b = ((y3 - y1) * (x + .5 - x3) + (x1 - x3) * (y + .5 - y3)) / d
                if a >= 0 and b >= 0 and a + b <= 1:
                    self.dot(x, y, col)

    def ring(self, cx, cy, rx, ry, col, keep=1.0, seed=0):
        for a10 in range(0, 3600, 6):
            if keep < 1 and hsh(seed, a10 // 60) > keep:
                continue
            a = math.radians(a10 / 10)
            self.dot(cx + rx * math.cos(a), cy + ry * math.sin(a), col)

    def bolt(self, x0, y0, x1, y1, ramp, seed, jag=3):
        # A jagged lightning bolt between two points, bright core with a dimmer fringe.
        n = max(3, int(math.hypot(x1 - x0, y1 - y0) / 4))
        pts = [(x0, y0)]
        for k in range(1, n):
            t = k / n
            nx, ny = -(y1 - y0), (x1 - x0)
            ln = math.hypot(nx, ny) or 1
            off = (hsh(seed, k) - 0.5) * 2 * jag
            pts.append((x0 + (x1 - x0) * t + nx / ln * off, y0 + (y1 - y0) * t + ny / ln * off))
        pts.append((x1, y1))
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            m = max(1, int(math.hypot(bx - ax, by - ay) * 1.5))
            for k in range(m + 1):
                x, y = ax + (bx - ax) * k / m, ay + (by - ay) * k / m
                self.dot(x + 1, y, ramp[2])
                self.dot(x, y + 1, ramp[2])
            for k in range(m + 1):
                self.dot(ax + (bx - ax) * k / m, ay + (by - ay) * k / m, ramp[0])


def write(name, frames, anchor, glow=False, fps=12, extra=None, charmap=None):
    os.makedirs(OUT, exist_ok=True)
    w, h = frames[0].w, frames[0].h
    pal, inv, rows_all = {}, {}, []
    for col, ch in (charmap or {}).items():                                      # reserved characters (dye zones)
        pal[ch], inv[col] = col, ch
    chars = iter("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
    for fr in frames:
        rows = []
        for y in range(h):
            line = ""
            for x in range(w):
                c = fr.px.get((x, y))
                if c is None:
                    line += "."
                    continue
                if c not in inv:
                    inv[c] = next(chars)
                    pal[inv[c]] = c
                line += inv[c]
            rows.append(line)
        rows_all.append(rows)
    d = {"width": w, "height": h, "fps": fps, "palette": pal, "dye_zones": {}, "attach": {},
         "anchor": anchor, "glow": glow, "animations": {name.split("/")[-1]: rows_all}}
    d.update(extra or {})
    os.makedirs(os.path.dirname(f"{OUT}/{name}.json"), exist_ok=True)
    json.dump(d, open(f"{OUT}/{name}.json", "w"))


# ============================================================================ element effects
def impact(el, S, f):
    # Hammer impact [5]: a flash at the hit point, a burst of the element flying out, then fading bits.
    W_ = H_ = 32 * S
    fx = FX(W_, H_)
    c = W_ / 2
    R = RAMPS[el]
    t = (f + 1) / 5
    if f == 0:
        fx.blob(c, c, 4 * S, R)
        for k in range(8):
            a = math.radians(k * 45 + 22)
            fx.streak(c, c, c + 7 * S * math.cos(a), c + 7 * S * math.sin(a), R)
        return fx
    n = 10
    for k in range(n):
        a = math.radians(k * 360 / n + hsh(el, k) * 30)
        d = (4 + 10 * t * (0.7 + 0.5 * hsh(el, k, 1))) * S
        x, y = c + d * math.cos(a), c + d * math.sin(a) + (f * f * 0.4 * S if el in ("earth", "water") else 0)
        fade = f >= 3
        if el == "fire":                                                         # flame tongues and embers
            r = (3.2 - f * 0.6) * S * (0.7 + 0.5 * hsh(k))
            if r > 0.6:
                fx.blob(x, y - f * S, r, R if not fade else R[1:] + [R[3]])
            if k % 3 == 0:
                fx.dot(x + 3 * S * math.cos(a), y + 3 * S * math.sin(a) - 2 * S, R[0])
        elif el == "water":                                                      # droplets in a crown, then a spray
            r = (2.6 - f * 0.4) * S
            if r > 0.6:
                fx.blob(x, y, r, R)
            fx.dot(x - math.cos(a) * 2 * S, y - math.sin(a) * 2 * S, R[1])
        elif el == "lightning":                                                  # jagged forks
            if f < 4:
                fx.bolt(c, c, x, y, R, (el, k, f), jag=2 * S)
            elif k % 2 == 0:
                fx.dot(x, y, R[1])
        elif el == "earth":                                                      # rock chunks and dust
            r = (2.4 - f * 0.25) * S
            fx.tri([(x - r, y + r), (x + r, y + r * 0.6), (x + r * 0.2, y - r)], R[1] if k % 2 else R[2])
            fx.dot(x - r * 0.4, y, R[0])
            if f >= 2 and k % 4 == 0:                                            # a few dust puffs drifting up
                fx.blob(c + (k - 4) * 3 * S, c + (6 - f * 2) * S, (1.4 + f * 0.6) * S, RAMPS["dust"][1:] + ["#5f7a3a"])
        elif el == "ice":                                                        # shards flying out, a frost ring
            ln = (5 - f * 0.6) * S
            ex, ey = x + ln * math.cos(a), y + ln * math.sin(a)
            nx, ny = -math.sin(a) * 1.4 * S, math.cos(a) * 1.4 * S
            fx.tri([(x + nx, y + ny), (x - nx, y - ny), (ex, ey)], R[1] if k % 2 else R[0])
    if el == "ice" and f in (1, 2):
        fx.ring(c, c, 10 * t * S + 3 * S, 10 * t * S + 3 * S, R[0], keep=0.7, seed=f)
    if f in (1, 2):
        fx.blob(c, c, (4 - f) * S, R)
    return fx


def splash(el, S, f):
    # Ground-miss splash [4]: the element hits the floor and spreads along it. Anchor = bottom centre.
    W_, H_ = 40 * S, 20 * S
    fx = FX(W_, H_)
    c, g = W_ / 2, H_ - 2
    R = RAMPS[el]
    t = (f + 1) / 4
    spread = 16 * t * S
    for k in range(12):
        side = -1 if k % 2 else 1
        x = c + side * spread * (0.2 + 0.8 * hsh(el, k))
        if el == "fire":
            ht = (8 - f * 1.6) * S * (0.6 + 0.6 * hsh(el, k, 2))
            if ht > 1:
                fx.tri([(x - 2 * S, g), (x + 2 * S, g), (x + hsh(k) * 2 - 1, g - ht)], R[1 if ht > 4 * S else 2])
                fx.tri([(x - 1 * S, g), (x + 1 * S, g), (x, g - ht * 0.6)], R[0])
        elif el == "water":
            y = g - (6 * S * math.sin(math.pi * min(1, t * 1.3))) * (0.6 + 0.5 * hsh(k)) + f * 1.5 * S
            fx.blob(x, min(g, y), max(0.8, (2.2 - f * 0.3) * S), R)
            if f >= 2:
                for xx in range(int(c - spread), int(c + spread)):
                    fx.dot(xx, g + 1, R[2])
        elif el == "lightning":
            if f < 3:
                fx.bolt(c, g, x, g - hsh(k, f) * 6 * S, R, (k, f), jag=1.5 * S)
            fx.dot(x, g, R[1])
        elif el == "earth":
            y = g - 7 * S * math.sin(math.pi * t) * (0.5 + 0.6 * hsh(k))
            r = 1.6 * S
            fx.tri([(x - r, y + r), (x + r, y + r), (x, y - r)], R[1] if k % 2 else R[2])
            fx.blob(c + side * spread * 0.5, g - 2 * S, (2 + f) * S, RAMPS["dust"])
        elif el == "ice":
            ht = (6 - abs(x - c) / (spread + 1) * 4) * S * (0.6 + 0.6 * hsh(k)) * (1 if f < 3 else 0.6)
            fx.tri([(x - 1.5 * S, g), (x + 1.5 * S, g), (x, g - ht)], R[0] if k % 3 == 0 else R[1])
            for xx in range(int(c - spread), int(c + spread)):
                fx.dot(xx, g + 1, R[2])
    return fx


def aura(el, S, f):
    # Enemy aura loop [3]: motes of the element rising around an enemy. Anchor = bottom centre.
    W_ = H_ = 40 * S
    fx = FX(W_, H_)
    R = RAMPS[el]
    for k in range(14):
        base_x = (hsh(el, k) * 0.8 + 0.1) * W_
        phase = (f + k) % 3
        y = H_ - 4 * S - (hsh(el, k, 3) * 26 + phase * 4) * S
        x = base_x + math.sin(k + phase) * 2 * S
        edge = abs(x - W_ / 2) / (W_ / 2)
        if edge < 0.35 and y > H_ * 0.35:
            continue                                                             # keep the middle clear: that's the enemy
        if el == "fire":
            fx.tri([(x - 1.5 * S, y + 2 * S), (x + 1.5 * S, y + 2 * S), (x, y - (2 + phase) * S)], R[phase])
        elif el == "water":
            fx.blob(x, y, 1.3 * S, R)
        elif el == "lightning":
            if (k + f) % 2 == 0:
                fx.bolt(x, y, x + 3 * S, y - 4 * S, R, (k, f), jag=1.2 * S)
        elif el == "earth":
            fx.tri([(x - 1.4 * S, y + 1.4 * S), (x + 1.4 * S, y + 1 * S), (x, y - 1.4 * S)], R[k % 3])
        elif el == "ice":
            fx.dot(x, y, R[0])
            if phase == 1:
                for d in (1, -1):
                    fx.dot(x + d * S, y, R[1])
                    fx.dot(x, y + d * S, R[1])
    return fx


def build_element():
    for el in ELEMENTS:
        for size, S in SIZES.items():
            write(f"element/{el}_impact_{size}", [impact(el, S, f) for f in range(5)], [16 * S, 16 * S], el in GLOWING)
            write(f"element/{el}_splash_{size}", [splash(el, S, f) for f in range(4)], [20 * S, 20 * S - 2], el in GLOWING)
            write(f"element/{el}_aura_{size}", [aura(el, S, f) for f in range(3)], [20 * S, 40 * S - 1], el in GLOWING, fps=8)


# ============================================================================ Mind
def mind_cast(S, f):
    # Spell-cast burst [5] at the paws: runes spin up into a ring, then flare.
    W_ = H_ = 40 * S
    fx = FX(W_, H_)
    c = W_ / 2
    R = RAMPS["mind"]
    r = (4 + f * 3.5) * S
    for k in range(6 + f * 2):
        a = math.radians(k * 360 / (6 + f * 2) + f * 25)
        x, y = c + r * math.cos(a), c + r * math.sin(a)
        if f < 4:
            fx.blob(x, y, (1.6 - f * 0.15) * S, R)
        else:
            fx.dot(x, y, R[1])
    if f >= 2:
        fx.ring(c, c, r, r, R[2] if f < 4 else R[3], keep=0.8, seed=f)
    fx.blob(c, c, (3 if f in (2, 3) else 2) * S, R)
    if f == 3:
        for k in range(8):
            a = math.radians(k * 45)
            fx.streak(c, c, c + r * 1.2 * math.cos(a), c + r * 1.2 * math.sin(a), R)
    return fx


def mind_projectile(S, f):
    # Projectile [3 loop]: a purple orb with a wispy tail streaming behind it (it flies to the right).
    W_, H_ = 32 * S, 16 * S
    fx = FX(W_, H_)
    R = RAMPS["mind"]
    cx, cy = W_ - 7 * S, H_ / 2
    for k in range(10):
        t = k / 10
        x = cx - (4 + t * 18) * S
        y = cy + math.sin(t * 8 + f * 2.1) * 2.5 * S * t
        fx.blob(x, y, (3 - t * 2.4) * S, R[1:] + [R[3]] if t > 0.4 else R)
    fx.blob(cx, cy, 4.5 * S, R, core=0.5)
    fx.dot(cx - 1 * S, cy - 1.5 * S, "#ffffff")
    return fx


def mind_hit(S, f):
    # Impact [4]: the orb bursts into a ring and scattered motes.
    W_ = H_ = 32 * S
    fx = FX(W_, H_)
    c = W_ / 2
    R = RAMPS["mind"]
    r = (3 + f * 4) * S
    if f == 0:
        fx.blob(c, c, 5 * S, R)
    fx.ring(c, c, r, r, R[1] if f < 2 else R[2], keep=1 if f < 2 else 0.6, seed=f)
    for k in range(10):
        a = math.radians(k * 36 + 10)
        d = r * (0.6 + 0.5 * hsh(k))
        if f > 0:
            fx.blob(c + d * math.cos(a), c + d * math.sin(a), max(0.7, (2 - f * 0.4) * S), R)
    return fx


def build_mind():
    for size, S in SIZES.items():
        write(f"mind/cast_{size}", [mind_cast(S, f) for f in range(5)], [20 * S, 20 * S], True)
        write(f"mind/projectile_{size}", [mind_projectile(S, f) for f in range(3)], [25 * S, 8 * S], True)
        write(f"mind/impact_{size}", [mind_hit(S, f) for f in range(4)], [16 * S, 16 * S], True)


# ============================================================================ general
def hit_spark(f):
    fx = FX(24, 24)
    R = RAMPS["spark"]
    c = 12
    for k in range(6):
        a = math.radians(k * 60 + 15 + f * 10)
        d0, d1 = (0, 2 + f * 3) if f < 2 else (5 + f * 2, 8 + f * 2)
        fx.streak(c + d0 * math.cos(a), c + d0 * math.sin(a), c + d1 * math.cos(a), c + d1 * math.sin(a), R)
    if f == 0:
        fx.blob(c, c, 3, R)
    return fx


def level_up(f):
    # Level-up burst [6]: a column of golden light shoots up, a ring bursts outward, sparkles rain down.
    fx = FX(64, 80)
    R = RAMPS["gold"]
    cx, g = 32, 76
    if f <= 3:
        ht = min(76, 20 + f * 24)
        wd = (3, 6, 8, 6)[f]
        for y in range(g - ht, g):
            for dx in range(-wd, wd + 1):
                if abs(dx) < wd * 0.4:
                    fx.dot(cx + dx, y, R[0])
                elif (dx + y) % 2 == 0:
                    fx.dot(cx + dx, y, R[1])
    if 2 <= f <= 4:
        r = (f - 1) * 10
        fx.ring(cx, g - 4, r, r * 0.3, R[0])
        fx.ring(cx, g - 4, r - 2, (r - 2) * 0.3, R[1], keep=0.7, seed=f)
    for k in range(16):                                                          # sparkles
        if f < 2:
            continue
        x = cx + (hsh(k) - 0.5) * 56
        y = g - 70 * hsh(k, 1) + (f - 2) * 6
        if 0 <= y < 80:
            if (k + f) % 3 == 0:
                for d in (-1, 1):
                    fx.dot(x + d, y, R[1])
                    fx.dot(x, y + d, R[1])
            fx.dot(x, y, R[0])
    return fx


def build_general():
    write("general/hit_spark", [hit_spark(f) for f in range(3)], [12, 12], True)
    write("general/level_up", [level_up(f) for f in range(6)], [32, 76], True, fps=10)



# ============================================================================ Strength / Speed
def slam(S, f):
    # Ground-slam shockwave [5]: a ring of force racing out along the floor, rocks and dust kicked up.
    W_, H_ = 64 * S, 24 * S
    fx = FX(W_, H_)
    c, g = W_ / 2, H_ - 3
    R = RAMPS["bronze"]
    r = (6 + f * 7) * S
    fx.ring(c, g - 2 * S, r, r * 0.22, R[0] if f < 3 else R[1], keep=1 if f < 3 else 0.6, seed=f)
    fx.ring(c, g - 2 * S, r - 2 * S, (r - 2 * S) * 0.22, R[1], keep=0.8, seed=f + 9)
    for k in range(10):
        side = -1 if k % 2 else 1
        x = c + side * r * (0.5 + 0.5 * hsh(k))
        y = g - (6 + 8 * hsh(k, 1)) * S * math.sin(math.pi * min(1, (f + 1) / 4))
        if f < 4:
            sz = 1.6 * S
            fx.tri([(x - sz, y + sz), (x + sz, y + sz * 0.6), (x, y - sz)], RAMPS["earth"][k % 3])
    for k in range(4):
        fx.blob(c + (k - 1.5) * r * 0.5, g - 2 * S - f * S, (2 + f * 0.8) * S, RAMPS["dust"])
    if f == 0:
        for k in range(7):
            a = math.radians(180 + k * 30)
            fx.streak(c, g, c + 10 * S * math.cos(a), g + 6 * S * math.sin(a), R)
    return fx


def armor_up(S, f):
    # Armour-up shimmer [4]: bronze hexagon plates flicker into place round him, then a sweep of light.
    W_ = H_ = 48 * S
    fx = FX(W_, H_)
    c = W_ / 2
    R = RAMPS["bronze"]
    for k in range(10):
        a = math.radians(k * 36 + 18)
        if hsh(k, f) > (0.3 + f * 0.2):
            continue
        x, y = c + 16 * S * math.cos(a), c + 18 * S * math.sin(a)
        for j in range(6):                                                      # a little hexagon outline
            a0, a1 = math.radians(j * 60), math.radians(j * 60 + 60)
            fx.streak(x + 3 * S * math.cos(a0), y + 3 * S * math.sin(a0), x + 3 * S * math.cos(a1), y + 3 * S * math.sin(a1), R)
    band = -18 * S + f * 12 * S                                                   # the sweep of light, bottom to top
    for x in range(W_):
        y = int(c - band + (x - c) * 0.3)
        if 0 <= y < H_ and math.hypot(x - c, y - c) < 20 * S:
            fx.dot(x, y, R[0])
            fx.dot(x, y + 1, R[1])
    return fx


def slash(S, f):
    # Slash arc [3]: a crescent swipe of silver light, thick at the front, trailing to a thin tail.
    W_ = H_ = 40 * S
    fx = FX(W_, H_)
    c = W_ / 2
    R = RAMPS["silver"]
    a0, a1 = -110 + f * 25, 40 + f * 35
    for k in range(40):
        t = k / 39
        a = math.radians(a0 + (a1 - a0) * t)
        r = 15 * S
        th = (0.6 + 3.2 * t) * S * (1 - f * 0.25)
        for d in range(int(th) + 1):
            col = R[0] if d < th * 0.4 else R[1] if d < th * 0.8 else R[2]
            if f == 2 and hsh(k, d) < 0.4:
                continue
            fx.dot(c + (r - d) * math.cos(a), c + (r - d) * math.sin(a), col)
    return fx


def afterimage(S, f):
    # Afterimage trail [3]: speed lines streaming behind a dash (he dashes to the right).
    W_, H_ = 48 * S, 32 * S
    fx = FX(W_, H_)
    R = RAMPS["silver"]
    for k in range(9):
        y = (3 + k * 3.2) * S
        ln = (10 + 20 * hsh(k, f)) * S
        x1 = W_ - (2 + 6 * hsh(k, 2, f)) * S
        fx.streak(x1 - ln, y, x1, y, R[1:] + [R[3]] if k % 2 else R)
    return fx


# ============================================================================ signature smoke (dyeable)
def smoke_puff(fx, cx, cy, r):
    fx.blob(cx, cy, r, RAMPS["smoke"], core=0.35)


def smoke_idle(f):
    # Idle wisps [4 loop]: a few curls of his smoke drifting up off his back.
    fx = FX(24, 32)
    for k in range(4):
        ph = (f + k) % 4
        x = 12 + math.sin(ph * 1.4 + k) * 3
        y = 28 - ph * 6 - k * 2
        smoke_puff(fx, x, y, 2.6 - ph * 0.4)
    return fx


def smoke_flare(S, f):
    # Power-up flare [5]: smoke rushing in and bursting up in a column. Drawn in his smoke dye zone; the game
    # tints it toward the element or type in use (swap the s S t T ramp).
    W_, H_ = 48 * S, 64 * S
    fx = FX(W_, H_)
    c, g = W_ / 2, H_ - 4 * S
    if f < 2:
        for k in range(10):                                                     # drawn in towards him
            a = math.radians(k * 36)
            d = (20 - f * 8) * S
            smoke_puff(fx, c + d * math.cos(a), g - 16 * S + d * 0.6 * math.sin(a), 2.5 * S)
    else:
        for k in range(12):                                                     # bursting up
            t = k / 11
            y = g - t * (20 + (f - 2) * 14) * S
            x = c + math.sin(t * 9 + f) * (4 + t * 6) * S
            smoke_puff(fx, x, y, (5 - t * 3 - (f - 2) * 0.6) * S)
        if f == 2:
            for k in range(8):
                a = math.radians(k * 45 + 10)
                fx.streak(c, g - 12 * S, c + 16 * S * math.cos(a), g - 12 * S + 12 * S * math.sin(a), RAMPS["smoke"])
    return fx


def smoke_trail(S, f):
    # Speed trail [3]: a smear of smoke left behind as he runs (to the right).
    W_, H_ = 40 * S, 24 * S
    fx = FX(W_, H_)
    for k in range(8):
        t = k / 7
        x = W_ - 4 * S - t * 32 * S
        y = H_ / 2 + math.sin(t * 6 + f * 2) * 3 * S
        smoke_puff(fx, x, y, (5 - t * 3.5) * S)
    return fx


# ============================================================================ general (the rest)
def crit(f):
    # Crit flash [3]: a big four-point star burst, white-gold.
    fx = FX(40, 40)
    R = RAMPS["spark"]
    c = 20
    ln = (10, 18, 14)[f]
    for a in (0, 90, 180, 270):
        r = math.radians(a)
        fx.streak(c, c, c + ln * math.cos(r), c + ln * math.sin(r), R, w=2.2 - f * 0.6)
    for a in (45, 135, 225, 315):
        r = math.radians(a)
        fx.streak(c, c, c + ln * 0.5 * math.cos(r), c + ln * 0.5 * math.sin(r), R)
    if f < 2:
        fx.blob(c, c, 4 - f, R)
    else:
        fx.ring(c, c, 15, 15, R[2], keep=0.6, seed=3)
    return fx


def parry(f):
    # Parry flash [3]: a bright vertical clash line with sparks spraying both ways.
    fx = FX(32, 40)
    R = RAMPS["white"]
    c = 16
    if f < 2:
        for y in range(4 + f * 4, 36 - f * 4):
            fx.dot(c, y, R[0])
            fx.dot(c + 1, y, R[1])
    for k in range(10):
        side = -1 if k % 2 else 1
        a = math.radians((150 if side < 0 else 30) + (hsh(k) - 0.5) * 70)
        d0, d1 = 2 + f * 4, 6 + f * 5
        fx.streak(c + d0 * math.cos(a) * side * side, 20 + d0 * math.sin(a), c + d1 * math.cos(a), 20 + d1 * math.sin(a), RAMPS["spark"])
    return fx


def heal(f):
    # Heal sparkle [4]: soft teal crosses and motes rising round him.
    fx = FX(32, 40)
    R = RAMPS["heal"]
    for k in range(8):
        x = 4 + hsh(k) * 24
        y = 36 - ((hsh(k, 1) * 20 + f * 6) % 34)
        big = (k + f) % 3 == 0
        fx.dot(x, y, R[0])
        if big:
            for d in (1, 2):
                for dx, dy in ((d, 0), (-d, 0), (0, d), (0, -d)):
                    fx.dot(x + dx, y + dy, R[d])
    return fx


def patch_up(f):
    # Patch-up bandage poof [4]: a puff of white with a spinning bandage and a little plus.
    fx = FX(40, 40)
    c = 20
    for k in range(6):
        a = math.radians(k * 60 + f * 20)
        d = 6 + f * 3
        r = 4 - f * 0.7
        if r > 0.8:
            fx.blob(c + d * math.cos(a), c + d * math.sin(a), r, RAMPS["white"][1:] + ["#8a8494"])
    if f < 3:                                                                   # the bandage strip, twirling
        a = math.radians(f * 50)
        for t in range(-8, 9):
            x, y = c + t * math.cos(a), c - 4 + t * math.sin(a) * 0.5
            fx.dot(x, y, RAMPS["cloth"][0] if t % 4 else RAMPS["cloth"][2])
            fx.dot(x, y + 1, RAMPS["cloth"][1])
    if f >= 1:                                                                  # a little teal plus
        for d in range(-2, 3):
            fx.dot(c, c - 10 - f + d, RAMPS["heal"][1])
            fx.dot(c + d, c - 10 - f, RAMPS["heal"][1])
    return fx


def coin_pop(f):
    # Coin pop [3]: a coin springs up spinning and glints.
    fx = FX(16, 24)
    R = RAMPS["gold"]
    y = (16, 8, 4)[f]
    wd = (3, 1, 3)[f]
    for dy in range(-3, 4):
        for dx in range(-wd, wd + 1):
            fx.dot(8 + dx, y + dy, R[0] if dx < 0 and dy < 0 else R[1] if abs(dx) < wd else R[2])
    if f == 2:
        for d in (1, 2, 3):
            fx.dot(8 + 3 + d, y - 3 - d, R[0])
    return fx


def loot_shine(f):
    # Loot shine [4]: a diagonal glint sweeping across an item (24x24, laid over its icon).
    fx = FX(24, 24)
    band = f * 10 - 6
    for y in range(24):
        for x in range(24):
            d = (x + y) - (band + 12)
            if abs(d) < 2:
                fx.dot(x, y, "#ffffff" if abs(d) < 1 else "#ffe08a")
    if f == 3:
        for d in (-2, -1, 1, 2):
            fx.dot(19 + d, 4, "#ffffff")
            fx.dot(19, 4 + d, "#ffffff")
    return fx


def new_sparkle(f):
    # "New thing" sparkle [4 loop]: two little stars twinkling at a corner.
    fx = FX(16, 16)
    for k, (x, y) in enumerate(((10, 5), (5, 10))):
        ph = (f + k * 2) % 4
        ln = (1, 3, 2, 0)[ph]
        for d in range(1, ln + 1):
            col = "#ffffff" if d == 1 else "#ffe08a"
            for dx, dy in ((d, 0), (-d, 0), (0, d), (0, -d)):
                fx.dot(x + dx, y + dy, col)
        if ln:
            fx.dot(x, y, "#ffffff")
    return fx


def mini_evo(f):
    # Mini evolution smoke flash [6]: his smoke swirls in, flashes white, blows away.
    fx = FX(56, 64)
    c, cy = 28, 36
    if f < 3:
        for k in range(10):
            a = math.radians(k * 36 + f * 40)
            d = 20 - f * 6
            smoke_puff(fx, c + d * math.cos(a), cy + d * 0.8 * math.sin(a), 3 + f)
    if f == 3:
        fx.blob(c, cy, 14, RAMPS["white"], core=0.6)
    if f >= 4:
        for k in range(10):
            a = math.radians(k * 36 + 15)
            d = 12 + (f - 4) * 10
            smoke_puff(fx, c + d * math.cos(a), cy + d * 0.8 * math.sin(a), 4 - (f - 4) * 1.5)
        if f == 4:
            fx.ring(c, cy, 16, 13, "#ffffff", keep=0.8, seed=4)
    return fx


def evolution(f):
    # Evolution sequence [12]: light gathers into a silhouette glow (the game draws his body pure white during
    # frames 2-7), a pillar of light rises with smoke swirling round it, then a burst reveals the new form.
    fx = FX(80, 128)
    c, g = 40, 124
    W_ = RAMPS["white"]
    if f < 3:                                                                   # motes rising and gathering
        for k in range(18):
            x = c + (hsh(k) - 0.5) * (60 - f * 18)
            y = g - hsh(k, 1) * 60 - f * 8
            fx.dot(x, y, W_[k % 3])
    if 2 <= f <= 8:                                                              # the pillar of light
        wd = min(16, 3 + (f - 2) * 3)
        for y in range(0, g):
            for dx in range(-wd, wd + 1):
                if abs(dx) < wd * 0.45:
                    fx.dot(c + dx, y, W_[0])
                elif (dx + y + f) % 2 == 0:
                    fx.dot(c + dx, y, W_[1])
    if 3 <= f <= 9:                                                              # smoke swirling round it
        for k in range(14):
            t = k / 13
            a = t * 6.28 * 2 + f * 0.9
            y = g - 10 - t * 100
            x = c + math.cos(a) * (20 + 4 * math.sin(f + k))
            if math.sin(a) > -0.2:                                              # only the front half of the swirl
                smoke_puff(fx, x, y, 4 + (k % 3))
    if f >= 9:                                                                  # the burst reveal
        r = (f - 8) * 18
        fx.ring(c, g - 40, r, r * 0.9, W_[0], keep=1 if f < 11 else 0.5, seed=f)
        fx.ring(c, g - 40, r - 4, (r - 4) * 0.9, W_[2], keep=0.7, seed=f + 3)
        for k in range(16):
            a = math.radians(k * 22.5)
            d = r * (0.8 + 0.3 * hsh(k))
            fx.dot(c + d * math.cos(a), g - 40 + d * 0.9 * math.sin(a), "#ffe08a")
    return fx


def build_strength_speed():
    for size, S in SIZES.items():
        write(f"strength/slam_{size}", [slam(S, f) for f in range(5)], [32 * S, 24 * S - 3])
        write(f"strength/armor_up_{size}", [armor_up(S, f) for f in range(4)], [24 * S, 24 * S], True)
        write(f"speed/slash_{size}", [slash(S, f) for f in range(3)], [20 * S, 20 * S], True)
        write(f"speed/afterimage_{size}", [afterimage(S, f) for f in range(3)], [48 * S - 1, 16 * S])


def build_smoke():
    sm = {"dye_zones": {"smoke": "sStT"}}
    write("smoke/idle_wisps", [smoke_idle(f) for f in range(4)], [12, 31], fps=6, extra=sm, charmap=SMOKE_CHARS)
    for size, S in SIZES.items():
        write(f"smoke/power_flare_{size}", [smoke_flare(S, f) for f in range(5)], [24 * S, 64 * S - 4 * S],
              extra={**sm, "tint": "the game recolours s S t T toward the element or type in use"}, charmap=SMOKE_CHARS)
        write(f"smoke/speed_trail_{size}", [smoke_trail(S, f) for f in range(3)], [40 * S - 1, 12 * S], extra=sm,
              charmap=SMOKE_CHARS)


def build_general2():
    write("general/crit_flash", [crit(f) for f in range(3)], [20, 20], True)
    write("general/parry_flash", [parry(f) for f in range(3)], [16, 20], True)
    write("general/heal_sparkle", [heal(f) for f in range(4)], [16, 39], True, fps=8)
    write("general/patch_up", [patch_up(f) for f in range(4)], [20, 20])
    write("general/coin_pop", [coin_pop(f) for f in range(3)], [8, 23], True)
    write("general/loot_shine", [loot_shine(f) for f in range(4)], [12, 12], True)
    write("general/new_sparkle", [new_sparkle(f) for f in range(4)], [8, 8], True, fps=6)
    write("general/mini_evolution", [mini_evo(f) for f in range(6)], [28, 63], extra={"dye_zones": {"smoke": "sStT"}},
          charmap=SMOKE_CHARS)
    write("evolution/evolution", [evolution(f) for f in range(12)], [40, 124], True, fps=8,
          extra={"dye_zones": {"smoke": "sStT"}, "body_white_frames": [2, 7]}, charmap=SMOKE_CHARS)


def glow_sprites():
    # Soft-glow sprites (PNG with real alpha, for additive blending): fire, lightning, magic, eye glow,
    # each 3 flicker frames in one row.
    from PIL import Image
    kinds = {"fire": ((255, 160, 70), 32), "lightning": ((255, 240, 170), 32), "magic": ((190, 120, 255), 32),
             "eye": ((255, 70, 70), 16)}
    out = "art/out/effects/library/glow"
    os.makedirs(out, exist_ok=True)
    for name, ((r, g, b), size) in kinds.items():
        sheet = Image.new("RGBA", (size * 3, size))
        for f in range(3):
            im = Image.new("RGBA", (size, size))
            k = (1.0, 0.85, 0.93)[f]
            for y in range(size):
                for x in range(size):
                    d = math.hypot(x + .5 - size / 2, y + .5 - size / 2) / (size / 2)
                    a = max(0.0, 1 - d) ** 1.8 * k
                    im.putpixel((x, y), (r, g, b, int(a * 230)))
            sheet.paste(im, (f * size, 0))
        sheet.save(f"{out}/glow_{name}.png")
    print("glow sprites")


GROUPS = {"element": build_element, "mind": build_mind, "general": build_general, "strength_speed": build_strength_speed,
          "smoke": build_smoke, "general2": build_general2}


def render_all():
    import subprocess
    from PIL import Image, ImageFilter, ImageChops
    for root, _, files in os.walk(OUT):
        for fn in files:
            if not fn.endswith(".json"):
                continue
            src = os.path.join(root, fn)
            out = src.replace("art/source", "art/out").replace("\\", "/")[:-5]
            subprocess.run([sys.executable, "tools/render.py", src, "--out", out], check=True, capture_output=True)
            if json.load(open(src)).get("glow"):
                # the soft-glow layer: blur the sheet, brighten it, keep it soft (additive in game)
                sh = Image.open(f"{out}/sheet.png").convert("RGBA")
                blur = sh.filter(ImageFilter.GaussianBlur(3))
                r, g, b, a = blur.split()
                a = a.point(lambda v: min(255, int(v * 1.6)))
                Image.merge("RGBA", (r, g, b, a)).save(f"{out}/glow.png")
    print("rendered")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if "--render" in sys.argv:
        render_all()
        glow_sprites()
    else:
        for g in args or list(GROUPS):
            GROUPS[g]()
        print("built")
