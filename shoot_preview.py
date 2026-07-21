"""Screenshot preview.html (GitHub-rendered README + GH markdown CSS).

Run: uv run --with playwright python shoot_preview.py

Loads via file:// from the repo root so the relative assets/ images resolve,
exactly as they will on the profile page.
"""
import pathlib
from playwright.sync_api import sync_playwright

url = pathlib.Path("preview.html").resolve().as_uri()

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1100, "height": 1000}, device_scale_factor=2)
    pg.goto(url, wait_until="networkidle", timeout=60000)
    pg.wait_for_timeout(2500)
    pg.screenshot(path="preview-full.png", full_page=True)
    n = pg.evaluate("""() => {
        const im = [...document.images];
        return JSON.stringify({
            total: im.length,
            broken: im.filter(i => !i.complete || i.naturalWidth === 0)
                      .map(i => i.getAttribute('src')),
        });
    }""")
    print("images:", n)
    print("wrote preview-full.png")
    b.close()
