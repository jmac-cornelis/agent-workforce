#!/usr/bin/env python3
"""Publish all agent workforce pages to Confluence.

Reads agent plan markdown from ``docs/workforce/`` and draw.io diagrams from
``docs/diagrams/workforce/``, converts them to Confluence storage format, and
publishes each agent as a child page under the AI Agent Workforce parent page.

Pre-rendered diagram screenshots are read from ``docs/confluence/images/``
(produced by ``render_all_diagrams.py``).
"""
import sys, os, re, json

# ---------------------------------------------------------------------------
# Repo-relative paths — resolve from this script's location so the script
# works regardless of the caller's working directory.
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Ensure repo root is on sys.path so ``confluence_utils`` can be imported
# without requiring a separate checkout.
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from confluence_utils import connect_to_confluence
from PIL import Image, ImageChops

# Diagrams live under docs/diagrams/workforce/ after the repo consolidation.
DIAGRAM_DIR = os.path.join(REPO_ROOT, 'docs', 'diagrams', 'workforce')

# Agent plan markdown files live under docs/workforce/.
PLAN_DIR = os.path.join(REPO_ROOT, 'docs', 'workforce')

# Pre-rendered screenshot PNGs are stored here by render_all_diagrams.py.
IMG_DIR = os.path.join(REPO_ROOT, 'docs', 'confluence', 'images')

PARENT_PAGE_ID = '656572464'
SPACE_ID = '238190621'

AGENTS = [
    {'name': 'Ada', 'title': 'Ada — Test Planner Agent', 'plan': 'ADA_TEST_PLANNER_PLAN.md', 'diagram': 'ADA_USE_CASE.drawio', 'zone': 'Execution Spine', 'role': 'Test Planner', 'wave': 1, 'sprint': 'S3'},
    {'name': 'Curie', 'title': 'Curie — Test Generator Agent', 'plan': 'CURIE_TEST_GENERATOR_PLAN.md', 'diagram': 'CURIE_USE_CASE.drawio', 'zone': 'Execution Spine', 'role': 'Test Generator', 'wave': 1, 'sprint': 'S3'},
    {'name': 'Faraday', 'title': 'Faraday — Test Executor Agent', 'plan': 'FARADAY_TEST_EXECUTOR_PLAN.md', 'diagram': 'FARADAY_USE_CASE.drawio', 'zone': 'Execution Spine', 'role': 'Test Executor', 'wave': 1, 'sprint': 'S3'},
    {'name': 'Tesla', 'title': 'Tesla — Environment Manager Agent', 'plan': 'TESLA_TEST_ENVIRONMENT_MANAGER_PLAN.md', 'diagram': 'TESLA_USE_CASE.drawio', 'zone': 'Execution Spine', 'role': 'Environment Manager', 'wave': 1, 'sprint': 'S3'},
    {'name': 'Hedy', 'title': 'Hedy — Release Manager Agent', 'plan': 'HEDY_RELEASE_MANAGER_PLAN.md', 'diagram': 'HEDY_USE_CASE.drawio', 'zone': 'Execution Spine', 'role': 'Release Manager', 'wave': 4, 'sprint': 'S6'},
    {'name': 'Linus', 'title': 'Linus — Code Review Agent', 'plan': 'LINUS_CODE_REVIEW_AGENT_PLAN.md', 'diagram': 'LINUS_USE_CASE.drawio', 'zone': 'Execution Spine', 'role': 'Code Review', 'wave': 4, 'sprint': 'S6'},
    {'name': 'Babbage', 'title': 'Babbage — Version Manager Agent', 'plan': 'BABBAGE_VERSION_MANAGER_PLAN.md', 'diagram': 'BABBAGE_USE_CASE.drawio', 'zone': 'Intelligence & Knowledge', 'role': 'Version Manager', 'wave': 2, 'sprint': 'S4'},
    {'name': 'Linnaeus', 'title': 'Linnaeus — Traceability Agent', 'plan': 'LINNAEUS_TRACEABILITY_AGENT_PLAN.md', 'diagram': 'LINNAEUS_USE_CASE.drawio', 'zone': 'Intelligence & Knowledge', 'role': 'Traceability', 'wave': 2, 'sprint': 'S4'},
    {'name': 'Herodotus', 'title': 'Herodotus — Knowledge Capture Agent', 'plan': 'HERODOTUS_KNOWLEDGE_CAPTURE_AGENT_PLAN.md', 'diagram': 'HERODOTUS_USE_CASE.drawio', 'zone': 'Intelligence & Knowledge', 'role': 'Knowledge Capture', 'wave': 3, 'sprint': 'S5'},
    {'name': 'Hypatia', 'title': 'Hypatia — Documentation Agent', 'plan': 'HYPATIA_DOCUMENTATION_AGENT_PLAN.md', 'diagram': 'HYPATIA_USE_CASE.drawio', 'zone': 'Intelligence & Knowledge', 'role': 'Documentation', 'wave': 4, 'sprint': 'S7'},
    {'name': 'Nightingale', 'title': 'Nightingale — Bug Investigation Agent', 'plan': 'NIGHTINGALE_BUG_TRIAGE_REPRODUCTION_PLAN.md', 'diagram': 'NIGHTINGALE_USE_CASE.drawio', 'zone': 'Intelligence & Knowledge', 'role': 'Bug Investigation', 'wave': 4, 'sprint': 'S6'},
    {'name': 'Drucker', 'title': 'Drucker — Engineering Hygiene Agent', 'plan': 'DRUCKER_JIRA_COORDINATOR_PLAN.md', 'diagram': 'DRUCKER_USE_CASE.drawio', 'zone': 'Intelligence & Knowledge', 'role': 'Engineering Hygiene', 'wave': 5, 'sprint': 'S7'},
    {'name': 'Gantt', 'title': 'Gantt — Project Planner Agent', 'plan': 'GANTT_PROJECT_PLANNER_PLAN.md', 'diagram': 'GANTT_USE_CASE.drawio', 'zone': 'Planning & Delivery', 'role': 'Project Planner', 'wave': 5, 'sprint': 'S7'},
    {'name': 'Brooks', 'title': 'Brooks — Delivery Manager Agent', 'plan': 'BROOKS_DELIVERY_MANAGER_PLAN.md', 'diagram': 'BROOKS_USE_CASE.drawio', 'zone': 'Planning & Delivery', 'role': 'Delivery Manager', 'wave': 5, 'sprint': 'S8'},
]


def get_diagram_tab_names(drawio_path):
    with open(drawio_path, 'r') as f:
        content = f.read()
    return re.findall(r'<diagram[^>]*name="([^"]*)"', content)


def md_to_storage(plan_path, agent):
    with open(plan_path, 'r') as f:
        md = f.read()

    lines = md.strip().split('\n')
    sections = {}
    current_section = 'preamble'
    current_lines = []

    for line in lines:
        if line.startswith('## '):
            if current_lines:
                sections[current_section] = '\n'.join(current_lines).strip()
            current_section = line[3:].strip()
            current_lines = []
        elif line.startswith('# '):
            continue
        else:
            current_lines.append(line)
    if current_lines:
        sections[current_section] = '\n'.join(current_lines).strip()

    def md_section_to_html(text):
        html_parts = []
        in_list = False
        in_table = False
        table_rows = []

        for line in text.split('\n'):
            stripped = line.strip()

            if stripped.startswith('|') and '|' in stripped[1:]:
                if '---' in stripped:
                    continue
                cells = [c.strip() for c in stripped.split('|')[1:-1]]
                table_rows.append(cells)
                in_table = True
                continue
            elif in_table:
                header = table_rows[0]
                html_parts.append('<table data-layout="default"><tbody>')
                html_parts.append('<tr>' + ''.join(f'<th><p>{c}</p></th>' for c in header) + '</tr>')
                for row in table_rows[1:]:
                    html_parts.append('<tr>' + ''.join(f'<td><p>{c}</p></td>' for c in row) + '</tr>')
                html_parts.append('</tbody></table>')
                table_rows = []
                in_table = False

            if stripped.startswith('- ') or stripped.startswith('* '):
                if not in_list:
                    html_parts.append('<ul>')
                    in_list = True
                item = stripped[2:]
                item = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', item)
                item = re.sub(r'`(.+?)`', r'<code>\1</code>', item)
                html_parts.append(f'<li>{item}</li>')
            else:
                if in_list:
                    html_parts.append('</ul>')
                    in_list = False
                if stripped.startswith('### '):
                    html_parts.append(f'<h3>{stripped[4:]}</h3>')
                elif stripped == '---':
                    html_parts.append('<hr/>')
                elif stripped:
                    p = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', stripped)
                    p = re.sub(r'`(.+?)`', r'<code>\1</code>', p)
                    html_parts.append(f'<p>{p}</p>')

        if in_list:
            html_parts.append('</ul>')
        if in_table and table_rows:
            header = table_rows[0]
            html_parts.append('<table data-layout="default"><tbody>')
            html_parts.append('<tr>' + ''.join(f'<th><p>{c}</p></th>' for c in header) + '</tr>')
            for row in table_rows[1:]:
                html_parts.append('<tr>' + ''.join(f'<td><p>{c}</p></td>' for c in row) + '</tr>')
            html_parts.append('</tbody></table>')

        return '\n'.join(html_parts)

    name_lower = agent['name'].lower()
    # Diagrams are now under docs/diagrams/workforce/ in this repo.
    tab_names = get_diagram_tab_names(os.path.join(DIAGRAM_DIR, agent['diagram']))

    html = f'''<h1>{agent['title']}</h1>

<ac:structured-macro ac:name="toc" ac:schema-version="1">
<ac:parameter ac:name="maxLevel">2</ac:parameter>
</ac:structured-macro>

<p><ac:link><ri:page ri:content-title="AI Agent Workforce" /><ac:plain-text-link-body><![CDATA[Back to Agent Workforce Overview]]></ac:plain-text-link-body></ac:link></p>

<ac:structured-macro ac:name="info" ac:schema-version="1">
<ac:rich-text-body>
<p><strong>Zone:</strong> {agent['zone']} | <strong>Role:</strong> {agent['role']} | <strong>Wave:</strong> {agent['wave']} | <strong>Sprint:</strong> {agent['sprint']}</p>
</ac:rich-text-body>
</ac:structured-macro>
'''

    section_order = ['preamble'] + list(sections.keys())
    seen = set()

    for key in sections:
        if key in seen:
            continue
        seen.add(key)

        if key == 'preamble':
            if sections.get(key):
                html += f'\n<h2>Overview</h2>\n{md_section_to_html(sections[key])}'
            continue

        heading = key
        if 'diagram' in key.lower() or 'use case' in key.lower():
            continue

        html += f'\n<h2>{heading}</h2>\n{md_section_to_html(sections[key])}'

    html += '\n<h2>Use Case Diagrams</h2>\n'
    for i, tab_name in enumerate(tab_names):
        html += f'<h3>{tab_name}</h3>\n'
        html += f'<ac:image ac:align="center" ac:width="900"><ri:attachment ri:filename="{name_lower}-tab{i+1}.png" /></ac:image>\n'

    return html


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


def publish_agent(c, agent, screenshot_func=None):
    name_lower = agent['name'].lower()
    # Agent plan markdown is under docs/workforce/.
    plan_path = os.path.join(PLAN_DIR, agent['plan'])

    if not os.path.exists(plan_path):
        print(f"  SKIP: {plan_path} not found")
        return None

    print(f"\n=== Publishing {agent['title']} ===")

    body = md_to_storage(plan_path, agent)

    payload = {
        'spaceId': SPACE_ID,
        'status': 'current',
        'title': agent['title'],
        'parentId': PARENT_PAGE_ID,
        'body': {'representation': 'storage', 'value': body}
    }

    resp = c.session.post(f'{c.base_url}/api/v2/pages', json=payload)
    if resp.status_code in (200, 201):
        page = resp.json()
        page_id = page['id']
        print(f"  Created page {page_id}")
    elif resp.status_code == 409:
        print(f"  Page already exists, searching...")
        search_resp = c.session.get(f'{c.base_url}/api/v2/pages', params={
            'spaceId': SPACE_ID, 'title': agent['title'], 'status': 'current'
        })
        results = search_resp.json().get('results', [])
        if results:
            page_id = results[0]['id']
            ver = results[0]['version']['number']
            payload2 = {
                'id': page_id, 'status': 'current', 'title': agent['title'],
                'body': {'representation': 'storage', 'value': body},
                'version': {'number': ver + 1, 'message': 'Updated by publish script'}
            }
            resp2 = c.session.put(f'{c.base_url}/api/v2/pages/{page_id}', json=payload2)
            print(f"  Updated existing page {page_id}: {resp2.status_code}")
        else:
            print(f"  ERROR: Could not find or create page")
            return None
    else:
        print(f"  ERROR creating page: {resp.status_code} {resp.text[:300]}")
        return None

    # Upload pre-rendered diagram screenshots from docs/confluence/images/.
    img_files = sorted([f for f in os.listdir(IMG_DIR) if f.startswith(f'{name_lower}-tab') and f.endswith('.png')])
    for fname in img_files:
        fpath = os.path.join(IMG_DIR, fname)
        print(f"  Uploading {fname}...")
        with open(fpath, 'rb') as img:
            upload_resp = c.session.post(
                f'{c.base_url}/rest/api/content/{page_id}/child/attachment',
                headers={'X-Atlassian-Token': 'nocheck'},
                files={'file': (fname, img, 'image/png')},
                data={'minorEdit': 'true'}
            )
            print(f"    {upload_resp.status_code}")

    return page_id


if __name__ == '__main__':
    c = connect_to_confluence()

    for agent in AGENTS:
        page_id = publish_agent(c, agent)
        if page_id:
            print(f"  Done: {agent['title']} -> {page_id}")

    print("\n=== All agents published ===")
