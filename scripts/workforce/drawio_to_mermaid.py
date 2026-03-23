#!/usr/bin/env python3
"""
Convert AGENT_ORCHESTRATION_ZONES.drawio to a Mermaid block-beta diagram.

Source of truth: docs/diagrams/workforce/AGENT_ORCHESTRATION_ZONES.drawio
Outputs:
  - Mermaid block inserted into README.md and docs/AGENT_WORKFORCE_OVERVIEW.md
  - PNG rendered and uploaded to Confluence (separate step)

Usage:
    python3 scripts/drawio_to_mermaid.py

Reads the draw.io XML, extracts zones and their members, and generates
a Mermaid block-beta diagram that matches the draw.io layout.
"""

import re
import xml.etree.ElementTree as ET
import html
import sys
import os

DRAWIO_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'diagrams', 'workforce', 'AGENT_ORCHESTRATION_ZONES.drawio')

# Zone definitions: map zone background IDs to their config
ZONES = {
    'zone_ext':   {'header': 'ext_header',  'mermaid_id': 'ext',    'label': None, 'color': '#dae8fc', 'stroke': '#6c8ebf'},
    'zone_exec':  {'header': 'exec_header', 'mermaid_id': 'spine',  'label': None, 'color': '#d5e8d4', 'stroke': '#82b366'},
    'zone_intel': {'header': 'intel_header','mermaid_id': 'intel',  'label': None, 'color': '#e1d5e7', 'stroke': '#9673a6'},
    'zone_pm':    {'header': 'pm_header',   'mermaid_id': 'plan',   'label': None, 'color': '#f8cecc', 'stroke': '#b85450'},
    'zone_human': {'header': 'human_header','mermaid_id': 'humans', 'label': None, 'color': '#ffe6cc', 'stroke': '#d79b00'},
}

# Map zone background IDs to their x-range for membership detection
ZONE_RANGES = {}


def parse_drawio(path):
    """Parse the draw.io XML and extract zones and their members."""
    tree = ET.parse(path)
    root = tree.getroot()
    
    cells = {}
    for cell in root.iter('mxCell'):
        cell_id = cell.get('id')
        if cell_id:
            geom = cell.find('mxGeometry')
            x = float(geom.get('x', 0)) if geom is not None else 0
            y = float(geom.get('y', 0)) if geom is not None else 0
            w = float(geom.get('width', 0)) if geom is not None else 0
            h = float(geom.get('height', 0)) if geom is not None else 0
            value = cell.get('value', '')
            # Clean HTML from value
            value = re.sub(r'<[^>]+>', ' ', html.unescape(value)).strip()
            value = re.sub(r'\s+', ' ', value)
            style = cell.get('style', '')
            cells[cell_id] = {
                'id': cell_id, 'value': value, 'style': style,
                'x': x, 'y': y, 'w': w, 'h': h
            }
    
    # Extract zone backgrounds (x ranges)
    for zone_id, zone_cfg in ZONES.items():
        if zone_id in cells:
            c = cells[zone_id]
            ZONE_RANGES[zone_id] = (c['x'], c['x'] + c['w'])
        # Get header label
        header_id = zone_cfg['header']
        if header_id in cells:
            zone_cfg['label'] = cells[header_id]['value']
    
    # Classify each non-zone, non-header, non-legend, non-title cell into a zone
    skip_ids = set(['0', '1', 'title', 'subtitle', 'legend_title'])
    skip_ids.update(ZONES.keys())
    skip_ids.update(z['header'] for z in ZONES.values())
    skip_prefixes = ('leg',)
    
    zone_members = {zid: [] for zid in ZONES}
    
    for cid, c in cells.items():
        if cid in skip_ids or any(cid.startswith(p) for p in skip_prefixes):
            continue
        if not c['value'] or c['w'] == 0:
            continue
        
        # Find which zone this cell belongs to by x position
        cx = c['x'] + c['w'] / 2  # center x
        best_zone = None
        for zid, (zx0, zx1) in ZONE_RANGES.items():
            if zx0 <= cx <= zx1:
                best_zone = zid
                break
        
        if best_zone:
            zone_members[best_zone].append({
                'id': cid,
                'label': c['value'],
                'y': c['y']
            })
    
    # Sort members by y position within each zone
    for zid in zone_members:
        zone_members[zid].sort(key=lambda m: m['y'])
    
    return zone_members


def generate_mermaid(zone_members):
    """Generate Mermaid block-beta diagram from parsed zone data."""
    lines = ['```mermaid', 'block-beta', '    columns 5', '']
    
    zone_order = ['zone_ext', 'zone_exec', 'zone_intel', 'zone_pm', 'zone_human']
    
    for zid in zone_order:
        cfg = ZONES[zid]
        mid = cfg['mermaid_id']
        label = cfg['label'] or mid
        members = zone_members.get(zid, [])
        
        # Determine columns: 2 for zones with many members, 1 for small zones
        cols = 2 if len(members) > 3 else 1
        
        lines.append(f'    block:{mid}["{label}"]:1')
        lines.append(f'        columns {cols}')
        
        for m in members:
            safe_id = re.sub(r'[^a-zA-Z0-9]', '_', m['id'])
            # Format label with newline between name and role
            label_text = m['label'].replace(' ', '\\n', 1) if ' ' in m['label'] and len(m['label']) > 15 else m['label']
            lines.append(f'        {safe_id}["{label_text}"]')
        
        lines.append('')
    
    # Add styles
    for zid in zone_order:
        cfg = ZONES[zid]
        mid = cfg['mermaid_id']
        lines.append(f'    style {mid} fill:{cfg["color"]},stroke:{cfg["stroke"]}')
    
    lines.append('```')
    return '\n'.join(lines)


def update_md_file(filepath, mermaid_block):
    """Replace the zone map section in a markdown file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Find and replace the zone map section
    pattern = r'(## Agent Zone Map\n\n.*?\n\n)```mermaid\n.*?```'
    replacement = f'\\1{mermaid_block}'
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        print(f'  Updated: {filepath}')
    else:
        print(f'  No change: {filepath}')


def main():
    drawio_path = os.path.abspath(DRAWIO_PATH)
    print(f'Source: {drawio_path}')
    
    zone_members = parse_drawio(drawio_path)
    
    for zid, members in zone_members.items():
        label = ZONES[zid]['label']
        print(f'  {label}: {len(members)} members')
        for m in members:
            print(f'    - {m["label"]}')
    
    mermaid = generate_mermaid(zone_members)
    print(f'\nGenerated Mermaid ({len(mermaid)} chars)')
    print(mermaid)
    
    # Update MD files
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    readme = os.path.join(repo_root, 'README.md')
    overview = os.path.join(repo_root, 'docs', 'AGENT_WORKFORCE_OVERVIEW.md')
    
    print(f'\nUpdating MD files:')
    update_md_file(readme, mermaid)
    update_md_file(overview, mermaid)


if __name__ == '__main__':
    main()
