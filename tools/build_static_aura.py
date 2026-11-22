# Builds the Occultist's static-electricity aura (64x64) as a separate effect sprite that
# the game draws on top of his body (ART_BRIEF: effects are never baked in). For every one
# of his animations it makes a matching row with the same name and frame count, so the
# sparks follow each pose. Small jagged arcs crackle on a ring 2-3 px outside his
# silhouette, at new spots every frame, so it flickers. Colours: the lightning ramp.
# A glowing effect: the game should draw it with an additive soft glow as well.
# Usage: python tools/build_static_aura.py   (after tools/build_adult.py occultist)
#        python tools/render.py art/source/effects/occultist_static.json --out art/out/effects/occultist_static
import json, os, random

body = json.load(open("art/source/skerbie/adult_occultist.json"))
W, H = body["width"], body["height"]
PAL = {"W": "#ffffff", "Y": "#fff4b0", "Z": "#ffe14d"}  # lightning: core, glow, edge
N8 = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]


def ring(rows):
    # Pixels 2-3 px (chessboard distance) outside the silhouette.
    solid = {(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c != "."}
    near = lambda p, d: any((p[0] + dx, p[1] + dy) in solid
                            for dx in range(-d, d + 1) for dy in range(-d, d + 1))
    return {(x, y) for y in range(H) for x in range(W)
            if (x, y) not in solid and near((x, y), 3) and not near((x, y), 1)}


def aura(rows, seed):
    rnd = random.Random(seed)  # seeded, so the effect is the same every build
    halo = sorted(ring(rows))
    g = {}
    for _ in range(5):  # five jagged arcs crawling along the ring each frame
        p = rnd.choice(halo)
        path = [p]
        for _ in range(rnd.randint(6, 11) - 1):
            nxt = [q for q in ((p[0] + dx, p[1] + dy) for dx, dy in N8) if q in halo and q not in path]
            if not nxt:
                break
            # Prefer diagonal steps, so the arc zigzags instead of crawling in a smooth line.
            diag = [q for q in nxt if q[0] != p[0] and q[1] != p[1]]
            p = rnd.choice(diag if diag and rnd.random() < 0.7 else nxt)
            path.append(p)
        for k, q in enumerate(path):  # white-hot core along the middle, yellow at the ends
            g[q] = "Z" if k in (0, len(path) - 1) else ("W" if abs(k - len(path) // 2) <= 1 else "Y")
    for _ in range(2):  # a couple of loose sparks
        g[rnd.choice(halo)] = rnd.choice("YZ")
    return ["".join(g.get((x, y), ".") for x in range(W)) for y in range(H)]


anims = {name: [aura(rows, 1000 + 37 * a + i) for i, rows in enumerate(frames)]
         for a, (name, frames) in enumerate(body["animations"].items())}
os.makedirs("art/source/effects", exist_ok=True)
json.dump({"width": W, "height": H, "fps": 10, "palette": PAL, "dye_zones": {}, "attach": {},
           "animations": anims}, open("art/source/effects/occultist_static.json", "w"), indent=1)
print(f"static aura for {len(anims)} Occultist animations")
