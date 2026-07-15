"""Extend the 4-panel work-strip to 5 panels by appending a map-poster cell.
The existing work-strip.png is 1200x140 with 4 equal cells. We keep those four
cells at their native size and add a 5th equal cell (so 5*240 = 1200 -> each cell
becomes 240 wide when rebuilt). Instead of re-cropping the original four sources
(not in-repo), rescale the existing strip's 4 cells into 4/5 of the new width and
cover-crop the map-poster band into the final fifth."""
from PIL import Image

OLD = Image.open("assets/work-strip.png").convert("RGB")  # 1200x140, 4 cells
ow, oh = OLD.size
H = oh
CELL = ow // 4               # 300 -> old cell width
NEWN = 5
NEWCELL = 240                # 1200 / 5
NEW_W = NEWCELL * NEWN       # 1200

def cover(im, w, h):
    iw, ih = im.size
    s = max(w / iw, h / ih)
    im2 = im.resize((round(iw * s), round(ih * s)), Image.LANCZOS)
    x = (im2.width - w) // 2
    y = (im2.height - h) // 2
    return im2.crop((x, y, x + w, y + h))

strip = Image.new("RGB", (NEW_W, H))
# Re-cover-crop each of the 4 existing cells to the new (narrower) cell width.
for i in range(4):
    cell = OLD.crop((i * CELL, 0, (i + 1) * CELL, H))
    strip.paste(cover(cell, NEWCELL, H), (i * NEWCELL, 0))
# 5th cell: map-poster band.
band = Image.open("assets/raw/map-poster-band.png").convert("RGB")
strip.paste(cover(band, NEWCELL, H), (4 * NEWCELL, 0))
strip.save("assets/work-strip.png")
print("wrote 5-panel assets/work-strip.png", strip.size)
