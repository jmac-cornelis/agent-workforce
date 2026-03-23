#!/usr/bin/env python3
"""Render all agent workforce draw.io diagrams to PNG screenshots.

Uses Playwright to open each draw.io diagram tab in a headless browser via a
local ``render_drawio.html`` page, captures a screenshot, and crops whitespace.

Diagrams are read from ``docs/diagrams/workforce/`` and screenshots are written
to ``docs/confluence/images/``.

Prerequisites:
  - A local HTTP server serving the repo root on port 8766
  - Node.js with the ``playwright`` package installed
  - Pillow (``pip install Pillow``)
"""
import subprocess, os, re, time, json
from PIL import Image, ImageChops

# ---------------------------------------------------------------------------
# Repo-relative paths — resolve from this script's location so the script
# works regardless of the caller's working directory.
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Diagrams live under docs/diagrams/workforce/ after the repo consolidation.
DIAGRAM_DIR = os.path.join(REPO_ROOT, 'docs', 'diagrams', 'workforce')

# Pre-rendered screenshot PNGs are stored here for upload by publish_all.py.
IMG_DIR = os.path.join(REPO_ROOT, 'docs', 'confluence', 'images')

# The render HTML page is served from the local HTTP server.  The URL path
# is relative to the repo root served on port 8766.
RENDER_HTML = 'http://localhost:8766/scripts/render_drawio.html'

AGENTS = [
    ('ada', 'ADA_USE_CASE.drawio', 4),
    ('curie', 'CURIE_USE_CASE.drawio', 3),
    ('faraday', 'FARADAY_USE_CASE.drawio', 4),
    ('tesla', 'TESLA_USE_CASE.drawio', 4),
    ('hedy', 'HEDY_USE_CASE.drawio', 4),
    ('linus', 'LINUS_USE_CASE.drawio', 4),
    ('babbage', 'BABBAGE_USE_CASE.drawio', 4),
    ('linnaeus', 'LINNAEUS_USE_CASE.drawio', 4),
    ('herodotus', 'HERODOTUS_USE_CASE.drawio', 4),
    ('hypatia', 'HYPATIA_USE_CASE.drawio', 4),
    ('nightingale', 'NIGHTINGALE_USE_CASE.drawio', 4),
    ('drucker', 'DRUCKER_USE_CASE.drawio', 4),
    ('gantt', 'GANTT_USE_CASE.drawio', 4),
    ('brooks', 'BROOKS_USE_CASE.drawio', 4),
]

def crop_image(path):
    img = Image.open(path)
    bg = Image.new(img.mode, img.size, (255, 255, 255))
    diff = ImageChops.difference(img, bg).convert('L')
    bbox = diff.getbbox()
    if bbox:
        pad = 20
        x0, y0 = max(0, bbox[0] - pad), max(0, bbox[1] - pad)
        x1, y1 = min(img.width, bbox[2] + pad), min(img.height, bbox[3] + pad)
        cropped = img.crop((x0, y0, x1, y1))
        cropped.save(path)
        return cropped.size
    return img.size

# Ensure the output directory exists.
os.makedirs(IMG_DIR, exist_ok=True)

total = sum(t for _, _, t in AGENTS)
done = 0

for name, diagram, tabs in AGENTS:
    for page in range(tabs):
        out = os.path.join(IMG_DIR, f'{name}-tab{page+1}.png')
        done += 1
        print(f'[{done}/{total}] {name} page {page}...', end=' ', flush=True)

        # The diagram file URL is relative to the repo root served on 8766.
        # Diagrams now live under docs/diagrams/workforce/.
        url = f'{RENDER_HTML}?file=http://localhost:8766/docs/diagrams/workforce/{diagram}&page={page}'

        js = f'''
const {{ chromium }} = require('playwright');
(async () => {{
    const browser = await chromium.launch();
    const page = await browser.newPage();
    await page.setViewportSize({{ width: 1200, height: 700 }});
    await page.goto('{url}', {{ waitUntil: 'networkidle', timeout: 30000 }});
    await page.waitForTimeout(3000);
    await page.screenshot({{ path: '{out}', fullPage: false }});
    await browser.close();
}})();
'''
        result = subprocess.run(['node', '-e', js], capture_output=True, text=True, timeout=45)
        if result.returncode != 0:
            print(f'FAIL: {result.stderr[:200]}')
            continue

        size = crop_image(out)
        print(f'OK ({size[0]}x{size[1]})')

print(f'\nDone: {done}/{total} screenshots')
