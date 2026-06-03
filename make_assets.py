"""Crop two thumbnails and stitch a thin work-strip from raw screenshots.
Run: uv run --with pillow python make_assets.py
Crop tuples tuned to the 1600x900 raw captures (see comments)."""
from PIL import Image

RAW = "assets/raw"
OUT = "assets"

# (left, upper, right, lower) — tuned after viewing the raw captures.
# 15-min map: colored choropleth sits center-right; skip the white title bar + grey margins.
FIFTEEN_BOX = (380, 70, 1230, 830)
# street-orientations: the row of rose plots ("Finland ->") is the visual hook, ~y 540-820.
STREET_BOX = (40, 540, 1560, 820)
# For the thumbnail, the headline + first roses reads best: include the big headline.
STREET_THUMB_BOX = (40, 60, 1240, 820)


def load(name, box):
    im = Image.open(f"{RAW}/{name}").convert("RGB")
    return im.crop(box) if box else im


def thumb(im, width=480):
    w, h = im.size
    return im.resize((width, max(1, round(h * width / w))), Image.LANCZOS)


fifteen = load("fifteen-min-full.png", FIFTEEN_BOX)
street_thumb_src = load("street-orientations-full.png", STREET_THUMB_BOX)
street_strip_src = load("street-orientations-full.png", STREET_BOX)

# Thumbnails
thumb(fifteen).save(f"{OUT}/thumb-fifteen-min.png")
thumb(street_thumb_src).save(f"{OUT}/thumb-street-orientations.png")


# Work-strip: 1200x140, two equal panels (roses | map), cover-cropped to fill.
def panel(im, w, h):
    iw, ih = im.size
    scale = max(w / iw, h / ih)
    im2 = im.resize((round(iw * scale), round(ih * scale)), Image.LANCZOS)
    x = (im2.width - w) // 2
    y = (im2.height - h) // 2
    return im2.crop((x, y, x + w, y + h))


STRIP_W, STRIP_H = 1200, 140
half = STRIP_W // 2
strip = Image.new("RGB", (STRIP_W, STRIP_H))
strip.paste(panel(street_strip_src, half, STRIP_H), (0, 0))
strip.paste(panel(fifteen, STRIP_W - half, STRIP_H), (half, 0))
strip.save(f"{OUT}/work-strip.png")
print("wrote thumb-fifteen-min.png, thumb-street-orientations.png, work-strip.png")
