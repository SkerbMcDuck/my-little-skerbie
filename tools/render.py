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
