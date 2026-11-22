# Builds the Warden's static-electricity aura (64x64, 4-frame loop) as a separate effect
# sprite that the game draws on top of his body (ART_BRIEF: effects are never baked in).
# Small jagged sparks crackle on a ring 2-3 px outside his silhouette, at new spots each
# frame, so it flickers. Colours: the lightning ramp (white, pale yellow, yellow).
# A glowing effect: the game should also draw it with an additive soft glow.
# Usage: python tools/build_static_aura.py [animation]   (default: idle)
#        python tools/render.py art/source/effects/warden_static.json --out art/out/effects/warden_static
import json, os, random, sys

ANIM = sys.argv[1] if len(sys.argv) > 1 else "idle"
body = json.load(open("art/source/skerbie/adult_warden.json"))
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


frames = []
for i, rows in enumerate(body["animations"][ANIM]):
    rnd = random.Random(1000 + i)  # seeded, so the effect is the same every build
    halo = sorted(ring(rows))
    g = {}
    for _ in range(5):  # five jagged arcs crawling along the ring each frame
        p = rnd.choice(halo)
        n = rnd.randint(6, 11)
        path = [p]
        for _ in range(n - 1):
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
    frames.append(["".join(g.get((x, y), ".") for x in range(W)) for y in range(H)])

os.makedirs("art/source/effects", exist_ok=True)
json.dump({"width": W, "height": H, "fps": 10, "palette": PAL, "dye_zones": {}, "attach": {},
           "animations": {"static_aura": frames}},
          open("art/source/effects/warden_static.json", "w"), indent=1)
print(f"static_aura[{len(frames)}] around the Warden's {ANIM}")
