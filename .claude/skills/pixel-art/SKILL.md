---
name: "pixel-art"
description: "Make game-ready pixel art (sprites, animations, sprite sheets, tiles, icons, effects) by drawing exact pixel grids in code and rendering them. Use for any pixel art request, especially My Little Skerbie assets."
---

# Pixel Art

Draw true pixel art: every pixel placed on purpose, exact palette, no blur. Art is authored as character grids in a JSON file, rendered to PNG with the script below, then visually checked before delivery.

## Workflow

1. **Read the brief first.** If the project has an art brief (for My Little Skerbie: `ART.md`), use its sizes, palette, frame counts and descriptions. Never guess a size the brief defines.
2. **Set the palette** as named slots, each a single character mapped to a hex color. `.` is always transparent. Characters get about 12–16 colors; the whole world about 32.
3. **Block the silhouette** at 1x before any detail. It must read clearly as a solid shape.
4. **Draw the frames** as grids (one string per row, one character per pixel). Every row in a frame is exactly the sprite width, and every frame is exactly the sprite height.
5. **Render** with `render.py` (below): a sheet at 1x, a scaled preview (nearest-neighbor only), a GIF per animation, and a frame-data JSON.
6. **Look at the preview** with the Read tool. Fix anything on the checklist, re-render, and look again. Never deliver art you haven't viewed.
7. **Deliver** the sheet, previews, GIFs and frame data together.

## Craft rules

- **Silhouette first.** It must be readable at 1x and recognizable as a black shape.
- **Outlines:** characters get a dark outline (darkest tone of the adjacent color, or the outline slot), with selective outlining where light hits. Backgrounds get soft or no outlines, so characters pop.
- **Light source: top-left**, consistent across every asset.
- **Shading ramps:** 3–4 tones per material. Hue-shift: shadows lean cooler (toward purple/teal), highlights lean warmer (toward amber/peach). Never just darken one hue.
- **Avoid:** pillow shading (shading inward from the outline), banding (parallel same-length color stripes), jaggies (uneven line steps; keep steps 1-1-1, 2-2-2 or a smooth 1-2-3 progression), orphan pixels, and semi-transparent pixels (except on glow layers).
- **Anti-aliasing:** minimal and manual only, on large curves.
- **Eyes and faces** carry the emotion. Spend detail there first.

## Animation rules

- **10 fps by default.** The frame counts come from the brief.
- **Anchor point:** feet (or base) stay on the same pixel row across frames unless the motion is a jump or float.
- **Squash and stretch** by 1 pixel for weight. **Secondary motion** (ears, tails, scarves, smoke) lags the body by 1 frame.
- **Loops must be seamless:** the last frame flows into the first.
- **Draw one facing direction;** the game flips it in code.
- **Attachment points** (hand, head, torso) are recorded per frame in the frame data, so gear and hats snap on.
- **Effects** (smoke, sparks, element hits) are separate sprites, never baked into the body. Glowing effects get a separate soft-glow layer.

## Dye zones (recolorable sprites)

- Each dye zone uses its **own reserved 4-shade ramp** (highlight, base, shadow, deep shadow) that no other part of the sprite uses.
- Give these slots distinct characters (for example `1 2 3 4` for main fur, `5 6 7 8` for accent fur, `e E f F` for eye glow, `s S t T` for smoke) and list them under `dye_zones` in the frame data.
- Use the **same slot characters across every form** of a character, so the game's ramp swap works everywhere.
- Outlines and gear are never in a dye zone.

## My Little Skerbie house style

Apply this whenever the work is for My Little Skerbie. `ART.md` wins if anything conflicts.

- **Canvas:** portrait 225×487 at 5× (1125×2436); Jungle Run landscape 487×225. Skerbie is 32×32 (baby), 48×48 (kid), 64×64 (adult). Icons 24×24. Tiles 16×16.
- **Skerbie:** an original dark, smoky psychic critter. Black or grey fur, dark grey accents, glowing red or smoky eyes. A four-legged baby, an in-between kid (crouched, half-upright) and a humanoid adult. His signature effect is smoke wisps, and his eyes glow brighter in the dark. **Never copy or closely resemble an existing character** (for example any Pokémon). Inspiration only; the design must clearly stand on its own.
- **World palette:** deep charcoal, slate blue and mossy dark green, with warm amber light from lanterns and the hearth. Lo-fi feel: soft contrast, dusky purple and teal shadows, warm pink and amber highlights. **Pure black is reserved for his fur.**
- **Color lanes:** red is for his eyes, danger and fire only. **Mind magic = bright purple.** Elements: fire orange, water teal, lightning yellow-white, earth brown-green, ice pale blue. Enemy eyes are sickly yellow-green; red on enemies appears only as attack-warning flashes.
- **Rarity** is shown by icon frame material: rough wood (common), silver (rare), gold with a soft glow (epic).
- **Type colors in the UI:** Speed silver, Strength rusted bronze, Mind purple.

## render.py

Write this script into the project (for example `tools/render.py`) if it isn't there yet, and install Pillow if needed (`pip install pillow`).

```python
# Render pixel-art JSON into a 1x sheet, a scaled preview, GIFs, and frame data.
# Usage: python render.py sprite.json [--scale 8] [--out out_dir]
import json, sys, os, argparse
from PIL import Image

def hex_rgba(h):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)

def frame_img(rows, pal, w, h, name, i):
    if len(rows) != h:
        sys.exit(f"{name}[{i}]: {len(rows)} rows, expected {h}")
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        if len(row) != w:
            sys.exit(f"{name}[{i}] row {y}: width {len(row)}, expected {w}")
        for x, c in enumerate(row):
            if c == '.':
                continue
            if c not in pal:
                sys.exit(f"{name}[{i}] row {y}: unknown palette char '{c}'")
            img.putpixel((x, y), hex_rgba(pal[c]))
    return img

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('--scale', type=int, default=8)
    ap.add_argument('--out', default=None)
    a = ap.parse_args()
    d = json.load(open(a.src))
    w, h, pal = d['width'], d['height'], d['palette']
    fps = d.get('fps', 10)
    out = a.out or os.path.splitext(a.src)[0]
    os.makedirs(out, exist_ok=True)
    anims = d['animations']
    cols = max(len(f) for f in anims.values())
    sheet = Image.new('RGBA', (w * cols, h * len(anims)), (0, 0, 0, 0))
    meta = {'width': w, 'height': h, 'fps': fps,
            'dye_zones': d.get('dye_zones', {}), 'animations': {}}
    for r, (name, frames) in enumerate(anims.items()):
        imgs = [frame_img(f, pal, w, h, name, i) for i, f in enumerate(frames)]
        for c, im in enumerate(imgs):
            sheet.paste(im, (c * w, r * h))
        meta['animations'][name] = {
            'row': r, 'frames': len(imgs),
            'attach': d.get('attach', {}).get(name, [])}
        big = [im.resize((w * a.scale, h * a.scale), Image.NEAREST) for im in imgs]
        big[0].save(os.path.join(out, f'{name}.gif'), save_all=True,
                    append_images=big[1:], duration=int(1000 / fps),
                    loop=0, disposal=2, transparency=0)
    sheet.save(os.path.join(out, 'sheet.png'))
    prev = Image.new('RGBA', sheet.size, (40, 38, 48, 255))
    prev.alpha_composite(sheet)
    prev.resize((sheet.width * a.scale, sheet.height * a.scale),
                Image.NEAREST).save(os.path.join(out, 'preview.png'))
    json.dump(meta, open(os.path.join(out, 'frames.json'), 'w'), indent=2)
    print(f'Rendered {len(anims)} animations to {out}/')

if __name__ == '__main__':
    main()
```

### Sprite JSON format

```json
{
  "width": 32, "height": 32, "fps": 10,
  "palette": {"o": "#141218", "1": "#3a3640", "2": "#26232b",
              "3": "#1b1920", "4": "#0d0c10", "e": "#ff3b3b"},
  "dye_zones": {"main_fur": ["1", "2", "3", "4"], "eye_glow": ["e"]},
  "attach": {"idle": [{"head": [16, 6], "hand": [22, 20], "torso": [16, 18]}]},
  "animations": {"idle": [["....32 chars....", "...32 rows total..."]]}
}
```

The preview is drawn on a dark backdrop (#28262f) because the game's scenes are dark. Also check each sprite against a light backdrop once, so the outlines are verified.

## Quality checklist (before delivering)

- [ ] The silhouette reads at 1x.
- [ ] Only palette colors are used. No stray or orphan pixels.
- [ ] The light source is top-left and consistent. No pillow shading or banding.
- [ ] Lines are clean (even steps, no jaggies).
- [ ] Dye-zone ramps are used only in their zones, with the same slots across forms.
- [ ] Animation anchors are stable, loops are seamless, and secondary motion lags 1 frame.
- [ ] Attachment points are recorded for every frame that needs gear.
- [ ] Effects and glow are separate from the body.
- [ ] The design is original, not a copy or near-copy of any existing character.
- [ ] The preview and GIFs were actually viewed with Read.