"""Build README thumbnails + the animated banner from raw site captures.

Run: uv run --with pillow python make_assets.py

Rewritten 2026-07-21. The previous version (plus make_strip5.py /
make_map_poster_asset.py) hard-coded pixel crop boxes against 1600x900
captures. The 2026-07 captures are 3200x1800 (device_scale=2),
so every crop here is expressed as FRACTIONS of the source (0..1) and works at
any capture scale. Outputs:
  * assets/thumb-<slug>.png   -- 480px wide hero thumbs, 900px for the 3 heroes
  * assets/gallery-<slug>.png -- 320px wide gallery tiles
  * assets/work-strip.gif     -- animated banner cycling the 9 projects
  * assets/work-strip.png     -- static fallback (first frame equivalent)
"""
from PIL import Image

RAW, OUT = "assets/raw", "assets"

# Fractional crops (left, upper, right, lower) as 0..1 of the source image.
# Tuned by eyeballing each raw capture -- see the notes per project.
CROPS = {
    # Amsterdam ripples: canal-ring radial structure, centred on the lit core.
    # Stop above the control chrome (y<0.72) so no UI buttons leak in.
    "world-ripples":      (0.16, 0.02, 0.82, 0.72),
    # Helsinki ripples: the coastal spine + dense downtown knot.
    "helsinki-ripples":   (0.26, 0.06, 0.76, 0.76),
    # Breathing: the full lit HSL network; skip the title block at top-left
    # and the controls at the bottom.
    "helsinki-breathing": (0.14, 0.10, 0.86, 0.85),
    # Citadels: the masthead + star-fort diagram is the whole pitch.
    "nguyen-citadels":    (0.14, 0.06, 0.86, 0.88),
    # Map poster: the Binh Thanh plate only -- crop OUT the dark editor panel
    # on the right (it starts at ~x 0.645) and the AOI toast at the bottom.
    "map-poster":         (0.02, 0.02, 0.63, 0.94),
    # --- older 1600x900 captures, same fractional treatment ---
    "fifteen-min":        (0.2375, 0.078, 0.769, 0.922),
    "street-orientations": (0.025, 0.067, 0.775, 0.911),
    # place-names: use the place-names-vn.png capture (Vietnam tab, "Long" lit)
    # -- more vivid than place-names-full.png, and it carries the
    # "Long - dragon, prosperity" caption which makes the thumb self-explanatory.
    # The country sits at x~0.40-0.53, so centre the band on it rather than
    # cover-cropping a portrait subject into landscape (that stranded Vietnam
    # off to one side with a dead void beside it).
    "place-names":        (0.13, 0.13, 0.80, 0.86),
    "binh-thanh":         (0.2375, 0.083, 0.6875, 0.778),
}

# slug -> raw filename stem
RAWNAME = {
    "world-ripples": "world-ripples-full.png",
    "helsinki-ripples": "helsinki-ripples-full.png",
    "helsinki-breathing": "helsinki-breathing-full.png",
    "nguyen-citadels": "nguyen-citadels-full.png",
    "map-poster": "map-poster-full.png",
    "fifteen-min": "fifteen-min-full.png",
    "street-orientations": "street-orientations-full.png",
    "place-names": "place-names-vn.png",
    "binh-thanh": "binh-thanh-full.png",
}

HEROES = ["map-poster", "world-ripples", "place-names"]
GALLERY = ["helsinki-ripples", "helsinki-breathing", "binh-thanh",
           "nguyen-citadels", "fifteen-min", "street-orientations"]
# Banner cycle order: lead with the heroes, then the rest.
BANNER = HEROES + GALLERY


def load_crop(slug):
    im = Image.open(f"{RAW}/{RAWNAME[slug]}").convert("RGB")
    w, h = im.size
    l, u, r, d = CROPS[slug]
    return im.crop((round(l * w), round(u * h), round(r * w), round(d * h)))


def resize_w(im, width):
    w, h = im.size
    return im.resize((width, max(1, round(h * width / w))), Image.LANCZOS)


def cover(im, w, h):
    """Scale to fill w x h, centre-crop the overflow."""
    iw, ih = im.size
    scale = max(w / iw, h / ih)
    im2 = im.resize((max(1, round(iw * scale)), max(1, round(ih * scale))),
                    Image.LANCZOS)
    x = (im2.width - w) // 2
    y = (im2.height - h) // 2
    return im2.crop((x, y, x + w, y + h))


crops = {slug: load_crop(slug) for slug in RAWNAME}

# Hero thumbs. Pin them all to ONE landscape ratio (900x560) -- left to their
# natural crops the heroes came out wildly different shapes (place-names is a
# portrait S-curve at 900x1147) and the hero row looked ragged.
for slug in HEROES:
    cover(crops[slug], 900, 560).save(f"{OUT}/thumb-{slug}.png")
for slug in GALLERY:
    cover(crops[slug], 320, 200).save(f"{OUT}/gallery-{slug}.png")

# Animated banner: one frame per project, cover-cropped to a wide letterbox.
# A 6:1 letterbox is BRUTAL -- cover-cropping the hero crops into it left the
# portrait subjects (Vietnam's S-curve especially) as a sliver in a sea of
# void. So the banner uses its OWN wide crops, aimed at whatever part of each
# capture is horizontally dense.
BANNER_CROPS = {
    "map-poster":         (0.04, 0.30, 0.62, 0.72),
    "world-ripples":      (0.16, 0.16, 0.82, 0.62),
    # Vietnam is portrait: take a wide band across the SOUTHERN cluster, where
    # the lit dots are densest, rather than the whole country.
    "place-names":        (0.24, 0.55, 0.72, 0.86),
    "helsinki-ripples":   (0.26, 0.28, 0.76, 0.72),
    "helsinki-breathing": (0.14, 0.28, 0.86, 0.74),
    "nguyen-citadels":    (0.14, 0.08, 0.86, 0.36),
    # binh-thanh / street-orientations carry TEXT, and a band that bisects a
    # glyph row reads as a rendering bug. These two are placed from MEASURED
    # ink bands (row-wise ink profile of the raw capture), not by eye:
    #   binh-thanh big-nums row  = y 0.262-0.296
    #   street-orientations roses = y 0.794-0.969
    # Each band gets padding so the cover-crop still lands on whole glyphs.
    "binh-thanh":         (0.25, 0.247, 0.675, 0.311),
    "fifteen-min":        (0.2375, 0.30, 0.769, 0.70),
    "street-orientations": (0.025, 0.783, 0.775, 0.975),
}


def banner_crop(slug):
    im = Image.open(f"{RAW}/{RAWNAME[slug]}").convert("RGB")
    w, h = im.size
    l, u, r, d = BANNER_CROPS[slug]
    return im.crop((round(l * w), round(u * h), round(r * w), round(d * h)))


BW, BH = 1200, 200
frames = [cover(banner_crop(s), BW, BH) for s in BANNER]
# Quantize to a shared adaptive palette so the GIF doesn't flicker between
# frames with very different colour casts (dark ripples vs cream citadels).
pal_frames = [f.convert("P", palette=Image.ADAPTIVE, colors=128) for f in frames]
pal_frames[0].save(
    f"{OUT}/work-strip.gif",
    save_all=True,
    append_images=pal_frames[1:],
    duration=1400,
    loop=0,
    optimize=True,
)
# Static fallback: a 3-panel strip of the heroes (what a GIF-less client sees).
static = Image.new("RGB", (BW, BH))
cw = BW // 3
for i, slug in enumerate(HEROES):
    x = i * cw
    w = BW - x if i == 2 else cw
    static.paste(cover(banner_crop(slug), w, BH), (x, 0))
static.save(f"{OUT}/work-strip.png")

print("heroes:", ", ".join(f"thumb-{s}.png" for s in HEROES))
print("gallery:", ", ".join(f"gallery-{s}.png" for s in GALLERY))
print("banner: work-strip.gif (%d frames), work-strip.png" % len(frames))
