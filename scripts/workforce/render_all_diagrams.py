#!/usr/bin/env python3
import subprocess, os, re, time, json
from PIL import Image, ImageChops

BASE = '/Users/johnmacdonald/code/other/agent_workforce'
IMG_DIR = os.path.join(BASE, 'docs/confluence/images')
RENDER_HTML = f'http://localhost:8766/scripts/render_drawio.html'

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

total = sum(t for _, _, t in AGENTS)
done = 0

for name, diagram, tabs in AGENTS:
    for page in range(tabs):
        out = os.path.join(IMG_DIR, f'{name}-tab{page+1}.png')
        done += 1
        print(f'[{done}/{total}] {name} page {page}...', end=' ', flush=True)
        
        url = f'{RENDER_HTML}?file=http://localhost:8766/diagrams/{diagram}&page={page}'
        
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
