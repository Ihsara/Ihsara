"""Crop four thumbnails and stitch a thin four-panel work-strip from raw screenshots.
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
# place-names (Vietnam tab, "Long" morpheme lit): the glowing teal S-shape of Vietnam is
# the hook; crop tight on the country + lit dragon-cluster + its label.
PLACENAMES_THUMB_BOX = (490, 130, 1000, 780)
# Same map; for the strip panel, center on the dense southern glow cluster (landscape-ish
# so the cover-crop doesn't over-zoom).
PLACENAMES_STRIP_BOX = (540, 420, 940, 700)
# binh-thanh: warm masthead -> "Bình Thạnh, filling in" + the three terracotta big-nums
# + the flat-then-a-leap growth curve. That sequence is the whole pitch.
BINHTHANH_THUMB_BOX = (380, 75, 1100, 700)
# For the strip, the title + subtitle + big-nums band (~2:1, matches the strip cell so the
# cover-crop lands cleanly on whole glyphs, not a sliced fragment).
BINHTHANH_STRIP_BOX = (400, 95, 1080, 420)


def load(name, box):
    im = Image.open(f"{RAW}/{name}").convert("RGB")
    return im.crop(box) if box else im


def thumb(im, width=480):
    w, h = im.size
    return im.resize((width, max(1, round(h * width / w))), Image.LANCZOS)


fifteen = load("fifteen-min-full.png", FIFTEEN_BOX)
street_thumb_src = load("street-orientations-full.png", STREET_THUMB_BOX)
street_strip_src = load("street-orientations-full.png", STREET_BOX)
placenames_thumb_src = load("place-names-full.png", PLACENAMES_THUMB_BOX)
placenames_strip_src = load("place-names-full.png", PLACENAMES_STRIP_BOX)
binhthanh_thumb_src = load("binh-thanh-full.png", BINHTHANH_THUMB_BOX)
binhthanh_strip_src = load("binh-thanh-full.png", BINHTHANH_STRIP_BOX)

# Thumbnails
thumb(fifteen).save(f"{OUT}/thumb-fifteen-min.png")
thumb(street_thumb_src).save(f"{OUT}/thumb-street-orientations.png")
thumb(placenames_thumb_src).save(f"{OUT}/thumb-place-names.png")
thumb(binhthanh_thumb_src).save(f"{OUT}/thumb-binh-thanh.png")


# Work-strip: 1200x140, four equal panels (roses | 15-min map | place-names | binh-thanh),
# each cover-cropped to fill its cell.
def panel(im, w, h):
    iw, ih = im.size
    scale = max(w / iw, h / ih)
    im2 = im.resize((round(iw * scale), round(ih * scale)), Image.LANCZOS)
    x = (im2.width - w) // 2
    y = (im2.height - h) // 2
    return im2.crop((x, y, x + w, y + h))


STRIP_W, STRIP_H = 1200, 140
panels = [street_strip_src, fifteen, placenames_strip_src, binhthanh_strip_src]
n = len(panels)
strip = Image.new("RGB", (STRIP_W, STRIP_H))
# Distribute width evenly; last panel absorbs the rounding remainder.
base = STRIP_W // n
x = 0
for i, src in enumerate(panels):
    w = STRIP_W - x if i == n - 1 else base
    strip.paste(panel(src, w, STRIP_H), (x, 0))
    x += w
strip.save(f"{OUT}/work-strip.png")
print("wrote thumb-fifteen-min.png, thumb-street-orientations.png, "
      "thumb-place-names.png, thumb-binh-thanh.png, work-strip.png")
