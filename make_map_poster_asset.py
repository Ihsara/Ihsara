"""Build the map-poster thumbnail + strip panel from the live Preview capture.
Run: uv run --with pillow python make_map_poster_asset.py
The raw frame is a 2x capture of the .xp-frame poster element (1272x1800).
A black "AOI available" toast sits in the bottom-right ~9%; crop it off."""
from PIL import Image

raw = Image.open("assets/raw/map-poster-frame.png").convert("RGB")
w, h = raw.size  # 1272 x 1800
# Trim the bottom band that carries the toast + the tiny "map-poster" watermark.
poster = raw.crop((0, 0, w, int(h * 0.90)))

def thumb(im, width=480):
    ww, hh = im.size
    return im.resize((width, max(1, round(hh * width / ww))), Image.LANCZOS)

# Portrait thumbnail for the hero card.
thumb(poster).save("assets/thumb-map-poster.png")

# Strip panel: center on the title band + upper map so a cover-crop to the strip
# cell (1200/5 wide x 140 tall ~ 8.6:1) lands on the "Bình Thạnh" headline + river.
# Take a wide horizontal band around the title (y ~ 8%-34% of the full frame).
band = raw.crop((0, int(h * 0.06), w, int(h * 0.36)))
band.save("assets/raw/map-poster-band.png")
print("wrote assets/thumb-map-poster.png and assets/raw/map-poster-band.png; poster size", poster.size)
