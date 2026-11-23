# Builds the UI art (ART_BRIEF §14). The art draws no text: the game uses one OFL pixel font.
# Usage: python tools/build_ui.py [--look]
#        then render each art/source/ui/<name>.json with tools/render.py
#
#   panel.json        the shared panel (stats, recap, chest, merchant, settings, dye studio): dark carved wood
#                     framing worn parchment, iron brackets at the corners. A 9-slice: "nine_slice" [left, top,
#                     right, bottom] are the fixed borders, the middle stretches (it's kept flat so it stretches
#                     cleanly). "opacity" is the slight translucency the brief asks for (the game applies it).
#   journal_page.json the recap card: a torn journal page with faint ruled lines (the doodle icons go on it).
#   stat_groove.json  a carved groove (9-slice horizontally) and stat_fill.json, the fill strips in Speed silver,
#                     Strength bronze and Mind purple (tile them along the groove), stat_pip.json the subtype rank
#                     pips (empty, filled).
#   icons.json        the small 16x16 UI icons, one row; "icon_names" lists them.
#   doodles.json      the recap's paw-scrawl doodles (gathered, built, found, raid, overflow), 16x16.
# Colours are from §3 (UI dark wood #3b2a22, parchment #bfae8c, iron #5a5e66).
import json, math, os, random, sys

OUT = "art/source/ui"
os.makedirs(OUT, exist_ok=True)
LOOK = "--look" in sys.argv
O = "#0f0d14"
WOOD = ["#7a5636", "#3b2a22", "#23212b", "#17151c"]          # light -> deep
PARCH = ["#bfae8c", "#a8945e", "#8b7a4a", "#5f7a3a"]
IRON = ["#c9cfd6", "#5a5e66", "#33303d", "#17151c"]
INK = "#3b2a22"


def noise(x, y, s):
    return random.Random(x * 7919 + y * 104729 + s * 31).random()


class Img:
    def __init__(self, w, h):
        self.w, self.h, self.px = w, h, {}

    def put(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h and c:
            self.px[(int(x), int(y))] = c


def write(name, frames, extra=None, anim=None):
    w, h = frames[0].w, frames[0].h
    pal, inv, rows_all = {}, {}, []
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
    d = {"width": w, "height": h, "fps": 1, "palette": pal, "dye_zones": {}, "attach": {},
         "animations": {anim or name: rows_all}}
    d.update(extra or {})
    json.dump(d, open(f"{OUT}/{name}.json", "w"))
    print("wrote", name)


# ============================================================================ the panel (9-slice)
def panel():
    S, B = 48, 12                                     # size, border
    im = Img(S, S)
    for y in range(S):
        for x in range(S):
            e = min(x, y, S - 1 - x, S - 1 - y)
            lit = x < S / 2 and y < S / 2 or (e == x and y < S - 8) or (e == y and x < S - 8)
            if e == 0:
                c = O
            elif e <= 2:                              # a bevelled outer rim, lit on the top and left
                c = "#a8945e" if (lit and e == 1) else WOOD[0]
            elif e == 3:                              # a carved groove running round the frame
                c = WOOD[3]
            elif e == 4:
                c = WOOD[0] if not lit else "#a8945e"
            elif e <= 6:                              # the frame's face, with grain
                c = WOOD[1] if noise(x // 2, y // 5, 1) > 0.2 else WOOD[2]
            elif e == 7:
                c = O                                 # where the wood meets the parchment
            else:                                     # worn parchment; the centre (e > B) stays flat so it stretches
                c = PARCH[0]
                if e < B and noise(x, y, 2) < 0.3 * (B - e) / (B - 7):
                    c = PARCH[1]                      # darker, worn edges
                if e == 8:
                    c = PARCH[2] if (x + y) % 2 else PARCH[1]
            im.put(x, y, c)
    for cx, cy in ((0, 0), (1, 0), (0, 1), (1, 1)):                          # iron corner brackets
        fx, fy = (1 if cx == 0 else -1), (1 if cy == 0 else -1)
        ox, oy = (0 if cx == 0 else S - 1), (0 if cy == 0 else S - 1)
        for t in range(14):
            for w_ in range(5):
                for (x, y) in ((ox + fx * t, oy + fy * w_), (ox + fx * w_, oy + fy * t)):
                    edge = t in (0, 13) or w_ in (0, 4)
                    col = O if edge else (IRON[0] if (w_ == 1 and fx > 0 and fy > 0) else IRON[1] if (fx > 0 or fy > 0) else IRON[2])
                    im.put(x, y, col)
        for (a, b) in ((2, 2), (10, 2), (2, 10)):                             # rivets
            im.put(ox + fx * a, oy + fy * b, IRON[0])
            im.put(ox + fx * a + fx, oy + fy * b + fy, IRON[3])
    return im


# ============================================================================ the journal page
def journal():
    W_, H_ = 168, 220
    im = Img(W_, H_)
    rnd = random.Random(4)
    top = [int(4 + 3 * math.sin(x * 0.31) + rnd.random() * 3) for x in range(W_)]      # torn top edge
    bot = [int(H_ - 5 - 3 * math.sin(x * 0.27 + 1) - rnd.random() * 3) for x in range(W_)]
    for x in range(W_):
        for y in range(top[x], bot[x] + 1):
            if x < 2 or x > W_ - 3:
                continue
            c = PARCH[0]
            if y in (top[x], bot[x]) or x in (2, W_ - 3):
                c = O
            elif y < top[x] + 3 or y > bot[x] - 3 or x < 6 or x > W_ - 7:
                c = PARCH[1] if (x + y) % 2 else PARCH[0]                 # ragged, darker margins
            elif noise(x, y, 7) < 0.012:
                c = PARCH[1]                                               # a few faint age specks
            im.put(x, y, c)
    for y in range(30, H_ - 20, 14):                                       # faint ruled lines
        for x in range(14, W_ - 12):
            if im.px.get((x, y)) == PARCH[0] and noise(x, y, 3) < 0.8:
                im.put(x, y, PARCH[1])
    for x in range(26, 27):                                                # the margin line
        for y in range(20, H_ - 14):
            if im.px.get((x, y)) in PARCH[:2]:
                im.put(x, y, "#f2a0b0" if y % 3 else PARCH[1])
    for (x, y) in ((140, 40), (40, 170), (120, 160)):                      # a couple of tea / paw smudges
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                if dx * dx + dy * dy <= 8 and im.px.get((x + dx, y + dy)) in PARCH[:2]:
                    im.put(x + dx, y + dy, PARCH[2] if dx * dx + dy * dy > 3 else PARCH[1])
    return im


# ============================================================================ stats: groove, fills, pips
def groove():
    W_, H_ = 64, 9
    im = Img(W_, H_)
    for y in range(H_):
        for x in range(W_):
            e = min(x, y, W_ - 1 - x, H_ - 1 - y)
            c = O if e == 0 else WOOD[0] if (e == 1 and y == H_ - 2) else WOOD[3] if (y == 1) else WOOD[2]
            im.put(x, y, c)
    return im


def fill(kind):
    ramp = {"speed": ["#ffffff", "#c9cfd6", "#8a8494", "#5a5e66"], "strength": ["#ffd08a", "#a8643a", "#7a5636", "#3b2a22"],
            "mind": ["#e2b8ff", "#c77dff", "#9b4dff", "#6a2cc9"]}[kind]
    im = Img(8, 5)                                                          # tiles along the groove's 5 px inner channel
    for y in range(5):
        for x in range(8):
            im.put(x, y, ramp[0] if y == 0 else ramp[1] if y < 3 else ramp[2] if y < 4 else ramp[3])
    im.put(3, 1, ramp[0])
    return im


def pip(filled):
    im = Img(7, 7)
    for y in range(7):
        for x in range(7):
            d = abs(x - 3) + abs(y - 3)
            if d <= 3:
                if d == 3:
                    im.put(x, y, O)
                elif filled:
                    im.put(x, y, "#ffe08a" if (x < 3 and y < 3) else "#f2c14e" if d < 2 else "#a8643a")
                else:
                    im.put(x, y, WOOD[3] if y < 3 else WOOD[2])
    return im


# ============================================================================ 16x16 icons
def icon(name):
    im = Img(16, 16)
    L, M, D = PARCH[0], PARCH[1], PARCH[2]

    def line(x0, y0, x1, y1, c=L, w=1):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for k in range(int(n * 2) + 1):
            t = k / (n * 2)
            for dx in range(w):
                for dy in range(w):
                    im.put(round(x0 + (x1 - x0) * t) + dx, round(y0 + (y1 - y0) * t) + dy, c)

    def disc(cx, cy, r, c=L, ring=False):
        for y in range(16):
            for x in range(16):
                d = math.hypot(x + .5 - cx, y + .5 - cy)
                if (ring and r - 1.2 < d <= r) or (not ring and d <= r):
                    im.put(x, y, c)

    if name == "settings":
        disc(8, 8, 5.5)
        for k in range(8):
            a = math.radians(k * 45)
            disc(8 + 6.2 * math.cos(a), 8 + 6.2 * math.sin(a), 1.4)
        disc(8, 8, 2.2, D)
    elif name == "home":
        for y in range(3, 9):
            for x in range(8 - (y - 3), 9 + (y - 3)):
                im.put(x, y, L)
        for y in range(8, 14):
            for x in range(4, 13):
                im.put(x, y, M if x > 8 else L)
        for y in range(10, 14):
            for x in (7, 8):
                im.put(x, y, D)
    elif name == "hint":                                                    # a little lantern
        line(8, 1, 8, 3, M)
        for y in range(4, 12):
            for x in range(5, 12):
                im.put(x, y, "#ffd08a" if 6 <= x <= 10 and 5 <= y <= 10 else M)
        for x in range(5, 12):
            im.put(x, 4, M)
            im.put(x, 12, M)
        im.put(8, 7, "#ffffff")
    elif name == "confirm":
        line(3, 8, 6, 12, L, 2)
        line(6, 12, 12, 3, L, 2)
    elif name == "back":
        line(10, 3, 5, 8, L, 2)
        line(5, 8, 10, 13, L, 2)
    elif name == "lock":
        disc(8, 6, 3.6, L, ring=True)
        disc(8, 6, 2.6, L, ring=True)
        for y in range(7, 14):
            for x in range(4, 13):
                im.put(x, y, L if y < 9 else M)
        im.put(8, 10, D)
        im.put(8, 11, D)
    elif name == "level_star":
        pts = []
        for k in range(10):
            r = 6.5 if k % 2 == 0 else 2.8
            a = math.radians(-90 + k * 36)
            pts.append((8 + r * math.cos(a), 8.5 + r * math.sin(a)))
        for y in range(16):
            for x in range(16):
                px, py, hit = x + .5, y + .5, False
                for i in range(10):
                    (x1, y1), (x2, y2) = pts[i], pts[i - 1]
                    if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
                        hit = not hit
                if hit:
                    im.put(x, y, "#ffe08a" if x < 8 and y < 9 else "#f2c14e")
    # outline everything
    filled = set(im.px)
    for (x, y) in list(filled):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in filled and 0 <= q[0] < 16 and 0 <= q[1] < 16:
                im.put(q[0], q[1], O)
    return im


LOOK_ICONS = ["settings", "home", "hint", "confirm", "back", "lock", "level_star"]

if __name__ == "__main__":
    write("panel", [panel()], {"nine_slice": [12, 12, 12, 12], "opacity": 0.92})
    write("journal_page", [journal()], {"opacity": 1.0})
    write("stat_groove", [groove()], {"nine_slice": [3, 0, 3, 0], "fill_channel": [2, 2, 5]})
    write("stat_fill", [fill(k) for k in ("speed", "strength", "mind")], {"fill_names": ["speed", "strength", "mind"]}, anim="fill")
    write("stat_pip", [pip(False), pip(True)], {"pip_names": ["empty", "filled"]}, anim="pip")
    if LOOK:
        write("icons_look", [icon(n) for n in LOOK_ICONS], {"icon_names": LOOK_ICONS}, anim="icons")
