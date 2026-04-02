#!/usr/bin/env python3
'''Render all agent workforce draw.io diagrams to PNG screenshots.

Uses the local ``drawio`` CLI to export each draw.io page as a PNG, then crops
excess whitespace to keep Confluence attachments readable.

Diagrams are read from ``docs/diagrams/workforce/`` and screenshots are written
to ``docs/confluence/images/``.

Prerequisites:
  - draw.io desktop CLI available as ``drawio``
  - Pillow (``pip install Pillow``)
'''
import os
import re
import subprocess
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

def _diagram_set(stem):
    return [
        ('use-case', f'{stem}_USE_CASE.drawio'),
        ('sequence', f'{stem}_SEQUENCE.drawio'),
    ]


AGENTS = [
    ('josephine', _diagram_set('JOSEPHINE')),
    ('galileo', _diagram_set('GALILEO')),
    ('curie', _diagram_set('CURIE')),
    ('faraday', _diagram_set('FARADAY')),
    ('tesla', _diagram_set('TESLA')),
    ('humphrey', _diagram_set('HUMPHREY')),
    ('linus', _diagram_set('LINUS')),
    ('mercator', _diagram_set('MERCATOR')),
    ('bernerslee', _diagram_set('BERNERSLEE')),
    ('pliny', _diagram_set('PLINY')),
    ('hemingway', _diagram_set('HEMINGWAY')),
    ('nightingale', _diagram_set('NIGHTINGALE')),
    ('drucker', _diagram_set('DRUCKER')),
    ('gantt', _diagram_set('GANTT')),
    ('shackleton', _diagram_set('SHACKLETON')),
    ('shannon', _diagram_set('SHANNON')),
    ('blackstone', _diagram_set('BLACKSTONE')),
]


def get_diagram_tab_names(drawio_path):
    with open(drawio_path, 'r') as f:
        content = f.read()
    return re.findall(r'<diagram[^>]*name="([^"]*)"', content)

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

total = 0
for _, diagrams in AGENTS:
    for _, diagram in diagrams:
        total += len(get_diagram_tab_names(os.path.join(DIAGRAM_DIR, diagram)))
done = 0

for name, diagrams in AGENTS:
    for kind, diagram in diagrams:
        tabs = get_diagram_tab_names(os.path.join(DIAGRAM_DIR, diagram))
        for page in range(len(tabs)):
            out = os.path.join(IMG_DIR, f'{name}-{kind}-tab{page+1}.png')
            done += 1
            print(f'[{done}/{total}] {name} {kind} page {page + 1}...', end=' ', flush=True)

            diagram_path = os.path.join(DIAGRAM_DIR, diagram)
            result = subprocess.run(
                [
                    'drawio',
                    '-x',
                    '-f',
                    'png',
                    '--crop',
                    '-p',
                    str(page + 1),
                    '-o',
                    out,
                    diagram_path,
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != 0:
                print(f'FAIL: {result.stderr[:200]}')
                continue

            size = crop_image(out)
            print(f'OK ({size[0]}x{size[1]})')

print(f'\nDone: {done}/{total} screenshots')
