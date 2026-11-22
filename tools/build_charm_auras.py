# Builds the charm auras (ART_BRIEF §5): when Skerbie wears a charm, its element wraps him.
# Each aura is a separate effect sprite drawn over his body (effects are never baked in),
# made from his own silhouette, so there is one set per kid and adult form with a row for
# every animation (same names and frame counts as the body). All are glowing effects: the
# game should also draw them with an additive soft glow.
#   ember shard -> fire       flames lick up off his top edges
#   moon coin   -> ice        frost sparkles twinkle around him
#   feather     -> lightning  jagged static arcs crawl along his outline
#   bone die    -> earth      pebbles and dust orbit him
#   fang        -> water      droplets drift down around him
#   eye stone   -> mind       purple wisps rise and curl
# Usage: python tools/build_charm_auras.py   (after the kid and adult builders)
#        then render each art/source/effects/charms/<element>_<form>.json with tools/render.py
import json, math, os, random

FORMS = ["kid_speed", "kid_strength", "kid_mind",
         "adult_stalker", "adult_juggernaut", "adult_occultist", "adult_warden"]
PALS = {  # each element's colours from the master palette (ART_BRIEF §3), bright -> deep
    "fire":      {"A": "#ffe08a", "B": "#ffb347", "C": "#ff7a1a", "D": "#c2410c"},
    "ice":       {"A": "#f2f9ff", "B": "#cfe9ff", "C": "#9fc9f0"},
    "lightning": {"A": "#ffffff", "B": "#fff4b0", "C": "#ffe14d"},
    "earth":     {"A": "#a8945e", "B": "#8b7a4a", "C": "#5f7a3a"},
    "water":     {"A": "#8ff0e6", "B": "#2ec4b6", "C": "#178f86"},
    "mind":      {"A": "#e2b8ff", "B": "#c77dff", "C": "#9b4dff", "D": "#6a2cc9"},
}
N8 = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]


def silhouette(rows):
    return {(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c != "."}


def ring(solid, w, h, lo=2, hi=3):
    near = lambda p, d: any((p[0] + dx, p[1] + dy) in solid for dx in range(-d, d + 1) for dy in range(-d, d + 1))
    return sorted((x, y) for y in range(h) for x in range(w)
                  if (x, y) not in solid and near((x, y), hi) and not near((x, y), lo - 1))


def put(g, p, c, solid, w, h):
    if 0 <= p[0] < w and 0 <= p[1] < h and p not in solid:
        g[p] = c


def fire(solid, halo, rnd, i, w, h):
    # Tongues rise from ring pixels that sit just above his body.
    tops = [p for p in halo if any((p[0], p[1] + d) in solid for d in (2, 3, 4))]
    g = {}
    for p in rnd.sample(tops, min(len(tops), 14)):
        tall = rnd.randint(3, 7)
        sway = rnd.choice((-1, 0, 1))
        for k in range(tall):
            c = "D" if k == 0 else "C" if k < tall - 3 else "B" if k < tall - 1 else "A"
            x = p[0] + (sway if k >= tall // 2 else 0)
            put(g, (x, p[1] - k), c, solid, w, h)
            if k < tall // 2:  # a wider base, so each flame reads as a tongue, not a line
                put(g, (x + 1, p[1] - k), "C" if k else "D", solid, w, h)
    return g


def ice(solid, halo, rnd, i, w, h):
    # Twinkling frost: small sparkle crosses; each one holds for two frames, then moves.
    g, r2 = {}, random.Random(rnd.random() if i % 2 == 0 else rnd.random())
    for p in random.Random(hash((len(halo), i // 2))).sample(halo, min(len(halo), 6)):
        bright = (hash(p) + i) % 2 == 0
        put(g, p, "A" if bright else "B", solid, w, h)
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            put(g, (p[0] + d[0], p[1] + d[1]), "C" if bright else "C", solid, w, h)
    for p in r2.sample(halo, min(len(halo), 3)):
        put(g, p, "B", solid, w, h)
    return g


def lightning(solid, halo, rnd, i, w, h):
    # Jagged arcs crawling along the ring, white-hot in the middle.
    g, hs = {}, set(halo)
    for _ in range(5):
        p = rnd.choice(halo)
        path = [p]
        for _ in range(rnd.randint(6, 11) - 1):
            nxt = [q for q in ((p[0] + dx, p[1] + dy) for dx, dy in N8) if q in hs and q not in path]
            if not nxt:
                break
            diag = [q for q in nxt if q[0] != p[0] and q[1] != p[1]]
            p = rnd.choice(diag if diag and rnd.random() < 0.7 else nxt)
            path.append(p)
        for k, q in enumerate(path):
            g[q] = "C" if k in (0, len(path) - 1) else ("A" if abs(k - len(path) // 2) <= 1 else "B")
    for _ in range(2):
        g[rnd.choice(halo)] = rnd.choice("BC")
    return g


def earth(solid, halo, rnd, i, w, h):
    # Pebbles orbit: the ring is ordered by angle around his centre and the stones step along it.
    cx = sum(p[0] for p in solid) / len(solid)
    cy = sum(p[1] for p in solid) / len(solid)
    order = sorted(halo, key=lambda p: math.atan2(p[1] - cy, p[0] - cx))
    n, g = len(order), {}
    stone = [((0, 0), "A"), ((1, 0), "A"), ((-1, 1), "A"), ((0, 1), "B"), ((1, 1), "B"), ((2, 1), "C"),
             ((0, 2), "C"), ((1, 2), "C")]  # a chunky 4x3 stone, lit on its top-left
    for k in range(6):
        p = order[(k * n // 6 + i * 3) % n]
        for (dx, dy), c in (stone if k % 2 == 0 else stone[:5]):
            put(g, (p[0] + dx, p[1] + dy), c, solid, w, h)
        for t in (4, 7):  # a trail of dust behind each stone
            q = order[(k * n // 6 + i * 3 - t) % n]
            put(g, q, "B" if t == 4 else "C", solid, w, h)
    return g


def water(solid, halo, rnd, i, w, h):
    # Droplets drift down the ring, 1 px per frame, with a bright top and darker tail.
    g = {}
    seeds = random.Random(len(halo)).sample(halo, min(len(halo), 10))
    for k, p in enumerate(seeds):
        y = p[1] + (i + k) % 4
        # A drop: round 2 px head with a bright glint, narrowing into a tail above it.
        put(g, (p[0], y + 2), "B", solid, w, h)
        put(g, (p[0] + 1, y + 2), "C", solid, w, h)
        put(g, (p[0], y + 3), "C", solid, w, h)
        put(g, (p[0] + 1, y + 3), "C", solid, w, h)
        put(g, (p[0], y + 2), "A", solid, w, h)
        put(g, (p[0], y + 1), "B", solid, w, h)
        put(g, (p[0], y), "C", solid, w, h)
    return g


def mind(solid, halo, rnd, i, w, h):
    # Wisps: short trails that rise and curl, fading from bright to deep purple.
    g = {}
    for p in rnd.sample(halo, min(len(halo), 5)):
        curl = rnd.choice((-1, 1))
        for k, c in enumerate("ABBCD"):
            put(g, (p[0] + (curl if k in (2, 3) else 0) + (curl if k == 4 else 0), p[1] - k), c, solid, w, h)
    return g


STYLES = {"fire": fire, "ice": ice, "lightning": lightning, "earth": earth, "water": water, "mind": mind}

os.makedirs("art/source/effects/charms", exist_ok=True)
for form in FORMS:
    body = json.load(open(f"art/source/skerbie/{form}.json"))
    w, h = body["width"], body["height"]
    rings = {name: [ring(silhouette(f), w, h) for f in frames] for name, frames in body["animations"].items()}
    sils = {name: [silhouette(f) for f in frames] for name, frames in body["animations"].items()}
    for el, style in STYLES.items():
        anims = {}
        for a, (name, frames) in enumerate(body["animations"].items()):
            out = []
            for i in range(len(frames)):
                rnd = random.Random(f"{form}/{el}/{name}/{i}")  # deterministic per frame
                g = style(sils[name][i], rings[name][i], rnd, i, w, h)
                out.append(["".join(g.get((x, y), ".") for x in range(w)) for y in range(h)])
            anims[name] = out
        json.dump({"width": w, "height": h, "fps": 10, "palette": PALS[el], "dye_zones": {}, "attach": {},
                   "animations": anims}, open(f"art/source/effects/charms/{el}_{form}.json", "w"), indent=1)
    print(f"{form}: 6 auras x {len(body['animations'])} animations")
