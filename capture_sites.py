"""Capture raw 1600x900 screenshots of the live project sites.

Run: uv run --with playwright python capture_sites.py [slug ...]

Gotchas these settings encode (learned the hard way this session):
  * The ripple/transit pages boot behind an intro card. A naive shot catches the
    overlay over a near-empty canvas -- click "Explore" first. NOTE the overlay
    HIDES rather than detaching, so waiting for state="detached" always times
    out even though the click worked. Assert on the canvas instead.
  * WebGL does not render under plain headless Chromium -- the canvas came back
    as grey fog with a broken-image icon. Run HEADED with the GL flags below.
  * At the default 60x the ripples read as scattered dots. Kick speed to 300x
    and let it run so light ACCUMULATES into the "long exposure" look.
  * world-ripples and helsinki-ripples look identical on Helsinki -- put
    world-ripples on Amsterdam, since multi-city is the whole point of it.
Output goes to assets/raw/ (gitignored).
"""
import sys
from playwright.sync_api import sync_playwright

RAW = "assets/raw"

# Force real GL in a headed browser; SwiftShader as the software fallback.
GL_ARGS = [
    "--use-gl=angle",
    "--use-angle=default",
    "--enable-unsafe-swiftshader",
    "--ignore-gpu-blocklist",
    "--enable-gpu-rasterization",
]

# (slug, url, settle_ms, [click selectors in order])
SITES = [
    ("world-ripples", "https://ihsara.github.io/world-ripples/", 45000,
     ["text=Explore", "text=Amsterdam", "text=300×"]),
    ("helsinki-ripples", "https://ihsara.github.io/helsinki-ripples/", 45000,
     ["text=Explore", "text=300×"]),
    ("helsinki-breathing", "https://ihsara.github.io/helsinki-breathing/", 45000,
     ["text=Explore", "[data-speed='300']"]),
    ("nguyen-citadels", "https://ihsara.github.io/nguyen-citadels/", 6000, []),
    ("map-poster", "https://ihsara.github.io/map-poster/web/poster.html", 12000, []),
]

only = sys.argv[1:] or None

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=GL_ARGS)
    for slug, url, settle, clicks in SITES:
        if only and slug not in only:
            continue
        page = browser.new_page(viewport={"width": 1600, "height": 900},
                                device_scale_factor=2)
        print(f"-> {slug}: {url}")
        try:
            page.goto(url, wait_until="networkidle", timeout=90000)
        except Exception as e:
            print(f"   networkidle timed out ({type(e).__name__}), continuing")
        page.wait_for_timeout(3000)

        for sel in clicks:
            try:
                el = page.locator(sel).first
                el.wait_for(state="visible", timeout=20000)
                el.click()
                page.wait_for_timeout(1200)
                print(f"   clicked {sel}")
            except Exception as e:
                print(f"   !! click {sel}: {type(e).__name__}")

        page.wait_for_timeout(settle)

        try:
            info = page.evaluate("""() => {
                const c = document.querySelector('canvas');
                if (!c) return 'no canvas';
                const gl = c.getContext('webgl2') || c.getContext('webgl');
                return `canvas ${c.width}x${c.height} gl=${gl ? 'yes' : 'NO'}`;
            }""")
            print(f"   {info}")
        except Exception:
            pass

        out = f"{RAW}/{slug}-full.png"
        page.screenshot(path=out)
        print(f"   wrote {out}")
        page.close()
    browser.close()
print("done")
