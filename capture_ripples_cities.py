"""Capture all five world-ripples cities so the hero frame can be picked on evidence.

Run: uv run --with playwright python capture_ripples_cities.py [slug ...]

Why this exists: the profile README's world-ripples card was captured when the
app had only two cities, and it shows Amsterdam. The app now ships five. Rather
than guess which city photographs best, capture all of them and choose from a
measured contact sheet (see rank_ripples_cities.py).

Reuses the hard-won settings from capture_sites.py:
  * WebGL does NOT render under plain headless Chromium -- run HEADED with the
    ANGLE/SwiftShader flags.
  * The page boots behind an intro card; dismiss it via #intro-begin. The
    overlay HIDES rather than detaching, so never wait for state="detached".
    Do NOT use `text=Explore`: that ALSO matches the guided tour's Explore
    button, whose steps call setPaused(true). Captured that way the clock is
    frozen and no light accumulates -- which is exactly what the first run of
    this script produced (player stuck at 08:17, network reading as bare dots).
  * At the default speed the ripples read as scattered dots. Kick to 300x and
    let light ACCUMULATE into the long-exposure look.

City selection AND speed both use the app's OWN deep-link contract
(?city=<slug>&speed=300), not the chrome. Two reasons:
  * The switcher lives inside the places panel, which collapses on each switch,
    so clicking through it is far more fragile than a URL.
  * There is NO "300x" button to click. capture_sites.py's `text=300×` selector
    is a fossil from an older UI -- the speed control is a pair of steppers
    (id=speed-down / id=speed-up) around a readout, so that click has been
    silently timing out and every capture was taken at the 60x default. The
    deep link sets the speed before first paint instead.
"""
import sys
from playwright.sync_api import sync_playwright

RAW = "assets/raw"
BASE = "https://ihsara.github.io/world-ripples/"

GL_ARGS = [
    "--use-gl=angle",
    "--use-angle=default",
    "--enable-unsafe-swiftshader",
    "--ignore-gpu-blocklist",
    "--enable-gpu-rasterization",
]

CITIES = ["helsinki", "amsterdam", "berlin", "vienna", "zurich"]

SETTLE_MS = 45000

only = sys.argv[1:] or CITIES

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=GL_ARGS)
    for slug in only:
        url = f"{BASE}?city={slug}&speed=300"
        # 3200x1800 at device_scale_factor=1 -- NOT 1600x900 at dsf=2.
        # Both give a 3200x1800 PNG, but under dsf=2 this app renders the
        # network into roughly the top-left QUADRANT (measured: ink confined to
        # x[0.10,0.40] y[0.05,0.53], ~10% frame fill) while dsf=1 fills the
        # frame. Same URL, same settle. So ask for the big viewport directly.
        page = browser.new_page(viewport={"width": 3200, "height": 1800},
                                device_scale_factor=1)
        print(f"-> {slug}: {url}")
        try:
            page.goto(url, wait_until="networkidle", timeout=120000)
        except Exception as e:
            print(f"   networkidle timed out ({type(e).__name__}), continuing")
        page.wait_for_timeout(3000)

        for sel in ["#intro-begin"]:
            try:
                el = page.locator(sel).first
                el.wait_for(state="visible", timeout=20000)
                el.click()
                page.wait_for_timeout(1200)
                print(f"   clicked {sel}")
            except Exception as e:
                print(f"   !! click {sel}: {type(e).__name__}")

        page.wait_for_timeout(SETTLE_MS)

        # Confirm we are on the city we asked for AND that GL is live -- a
        # silent fallback to the landing default would otherwise produce five
        # Helsinki captures that all look plausible.
        try:
            info = page.evaluate("""() => {
                const c = document.querySelector('canvas');
                const gl = c && (c.getContext('webgl2') || c.getContext('webgl'));
                const sp = document.getElementById('speed-readout');
                const pp = document.getElementById('play-pause');
                return {
                  title: document.title,
                  canvas: c ? `${c.width}x${c.height}` : 'none',
                  gl: gl ? 'yes' : 'NO',
                  speed: sp ? sp.textContent.trim() : 'unknown',
                  // setPaused() flips aria-pressed (NOT aria-label, which is
                  // static markup): "true" means PAUSED.
                  paused: pp ? pp.getAttribute('aria-pressed') : 'unknown',
                  clock: (document.getElementById('clock') || {}).textContent,
                };
            }""")
            print(f"   {info}")
            if slug.lower() not in str(info.get("title", "")).lower():
                print(f"   !! WARNING: title {info.get('title')!r} does not name {slug}")
            # The whole point of the long settle is light ACCUMULATING at 300x.
            # A capture at the 60x default reads as scattered dots, and that
            # failure is invisible in the PNG unless you know what to look for.
            if "300" not in str(info.get("speed", "")):
                print(f"   !! WARNING: speed readout is {info.get('speed')!r}, expected 300×")
            # A paused capture is the failure that cost the first run: the tour's
            # Explore button freezes the clock, so the frame shows bare dots
            # instead of accumulated light.
            if str(info.get("paused")) == "true":
                print("   !! WARNING: player is PAUSED — no light accumulated")
        except Exception as e:
            print(f"   !! probe failed: {type(e).__name__}")

        out = f"{RAW}/wr-{slug}.png"
        page.screenshot(path=out)

        # Framing gate. A capture where the network hugs one corner is the
        # dsf=2 bug above, and it is NOT obvious in a thumbnail -- it just
        # looks like a sparse city. Measure the lit-ink bbox (excluding the
        # bottom chrome and the right PLACES tab) and complain if it does not
        # span a decent share of the frame.
        try:
            import numpy as np
            from PIL import Image
            a = np.asarray(Image.open(out).convert("L"), dtype=np.float32)
            h, w = a.shape
            a = a[:int(0.82 * h), :int(0.96 * w)]
            hh, ww = a.shape
            lit = a > np.median(a) + 12
            ys, xs = np.nonzero(lit)
            if len(xs):
                x1, x2 = np.percentile(xs, [1, 99]) / ww
                y1, y2 = np.percentile(ys, [1, 99]) / hh
                fill = (x2 - x1) * (y2 - y1)
                print(f"   ink x[{x1:.2f},{x2:.2f}] y[{y1:.2f},{y2:.2f}] fill={fill:.2f}")
                if fill < 0.25:
                    print(f"   !! WARNING: network fills only {fill:.0%} of frame "
                          "— check framing before using this capture")
            else:
                print("   !! WARNING: no lit pixels found")
        except Exception as e:
            print(f"   (framing check skipped: {type(e).__name__})")

        print(f"   wrote {out}")
        page.close()
    browser.close()
print("done")
