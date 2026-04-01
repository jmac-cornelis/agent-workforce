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

from confluence_utils import connect_to_confluence, _inline_markdown_to_storage
from PIL import Image, ImageChops

# Diagrams live under docs/diagrams/workforce/ after the repo consolidation.
DIAGRAM_DIR = os.path.join(REPO_ROOT, 'docs', 'diagrams', 'workforce')

# Agent plan markdown files now live under agents/<name>/docs/.
# Legacy PLAN_DIR kept for backward compat but individual agent entries
# can override via 'plan_path' (relative to REPO_ROOT).
PLAN_DIR = os.path.join(REPO_ROOT, 'docs', 'workforce')

# Pre-rendered screenshot PNGs are stored here by render_all_diagrams.py.
IMG_DIR = os.path.join(REPO_ROOT, 'docs', 'confluence', 'images')

PARENT_PAGE_ID = '656572464'
SPACE_ID = '238190621'

AGENTS = [
    {'name': 'Ada', 'title': 'Ada — Test Planner Agent', 'plan': 'agents/ada/docs/PLAN.md', 'diagram': 'ADA_USE_CASE.drawio', 'zone': 'Execution Spine', 'role': 'Test Planner', 'wave': 1, 'sprint': 'S3'},
    {'name': 'Curie', 'title': 'Curie — Test Generator Agent', 'plan': 'agents/curie/docs/PLAN.md', 'diagram': 'CURIE_USE_CASE.drawio', 'zone': 'Execution Spine', 'role': 'Test Generator', 'wave': 1, 'sprint': 'S3'},
    {'name': 'Faraday', 'title': 'Faraday — Test Executor Agent', 'plan': 'agents/faraday/docs/PLAN.md', 'diagram': 'FARADAY_USE_CASE.drawio', 'zone': 'Execution Spine', 'role': 'Test Executor', 'wave': 1, 'sprint': 'S3'},
    {'name': 'Tesla', 'title': 'Tesla — Environment Manager Agent', 'plan': 'agents/tesla/docs/PLAN.md', 'diagram': 'TESLA_USE_CASE.drawio', 'zone': 'Execution Spine', 'role': 'Environment Manager', 'wave': 1, 'sprint': 'S3'},
    {'name': 'Hedy', 'title': 'Hedy — Release Manager Agent', 'plan': 'agents/hedy/docs/PLAN.md', 'diagram': 'HEDY_USE_CASE.drawio', 'zone': 'Execution Spine', 'role': 'Release Manager', 'wave': 4, 'sprint': 'S6'},
    {'name': 'Linus', 'title': 'Linus — Code Review Agent', 'plan': 'agents/linus/docs/PLAN.md', 'diagram': 'LINUS_USE_CASE.drawio', 'zone': 'Execution Spine', 'role': 'Code Review', 'wave': 4, 'sprint': 'S6'},
    {'name': 'Babbage', 'title': 'Babbage — Version Manager Agent', 'plan': 'agents/babbage/docs/PLAN.md', 'diagram': 'BABBAGE_USE_CASE.drawio', 'zone': 'Intelligence & Knowledge', 'role': 'Version Manager', 'wave': 2, 'sprint': 'S4'},
    {'name': 'Linnaeus', 'title': 'Linnaeus — Traceability Agent', 'plan': 'agents/linnaeus/docs/PLAN.md', 'diagram': 'LINNAEUS_USE_CASE.drawio', 'zone': 'Intelligence & Knowledge', 'role': 'Traceability', 'wave': 2, 'sprint': 'S4'},
    {'name': 'Herodotus', 'title': 'Herodotus — Knowledge Capture Agent', 'plan': 'agents/herodotus/docs/PLAN.md', 'diagram': 'HERODOTUS_USE_CASE.drawio', 'zone': 'Intelligence & Knowledge', 'role': 'Knowledge Capture', 'wave': 3, 'sprint': 'S5'},
    {'name': 'Hypatia', 'title': 'Hypatia — Documentation Agent', 'plan': 'agents/hypatia/docs/PLAN.md', 'diagram': 'HYPATIA_USE_CASE.drawio', 'zone': 'Intelligence & Knowledge', 'role': 'Documentation', 'wave': 4, 'sprint': 'S7'},
    {'name': 'Nightingale', 'title': 'Nightingale — Bug Investigation Agent', 'plan': 'agents/nightingale/docs/PLAN.md', 'diagram': 'NIGHTINGALE_USE_CASE.drawio', 'zone': 'Intelligence & Knowledge', 'role': 'Bug Investigation', 'wave': 4, 'sprint': 'S6'},
    {'name': 'Drucker', 'title': 'Drucker — Engineering Hygiene Agent', 'plan': 'agents/drucker/docs/PLAN.md', 'diagram': 'DRUCKER_USE_CASE.drawio', 'zone': 'Engineering Hygiene', 'role': 'Engineering Hygiene', 'wave': 5, 'sprint': 'S7'},
    {'name': 'Gantt', 'title': 'Gantt — Project Planner Agent', 'plan': 'agents/gantt/docs/PLAN.md', 'diagram': 'GANTT_USE_CASE.drawio', 'zone': 'Planning & Delivery', 'role': 'Project Planner', 'wave': 5, 'sprint': 'S7'},
    {'name': 'Brooks', 'title': 'Brooks — Delivery Manager Agent', 'plan': 'agents/brooks/docs/PLAN.md', 'diagram': 'BROOKS_USE_CASE.drawio', 'zone': 'Planning & Delivery', 'role': 'Delivery Manager', 'wave': 5, 'sprint': 'S8'},
    {'name': 'Shannon', 'title': 'Shannon — Communications Agent', 'plan': 'agents/shannon/docs/PLAN.md', 'diagram': None, 'zone': 'Service Infrastructure', 'role': 'Communications', 'wave': 0, 'sprint': 'S1'},
    {'name': 'Brandeis', 'title': 'Brandeis — Legal Compliance Agent', 'plan': 'agents/brandeis/docs/PLAN.md', 'diagram': None, 'zone': 'Execution Spine', 'role': 'Legal Compliance', 'wave': 6, 'sprint': 'S9'},
]


def inline_md_to_storage(text):
    '''Render inline Markdown for Confluence user-doc publishing.

    Local repo markdown links do not resolve usefully in Confluence, so we
    degrade them to plain text (or inline code for path-like labels) before
    running the shared inline Markdown renderer.
    '''

    def _replace_local_link(match):
        label = match.group(1).strip()
        target = match.group(2).strip()
        if re.match(r'^[a-z]+://', target):
            return match.group(0)
        if target.startswith('#'):
            return match.group(0)
        if '/' in label or label.endswith('.md') or label == target:
            return f'`{label}`'
        return label

    normalized = re.sub(r'(?<!\!)\[([^\]]+)\]\(([^)]+)\)', _replace_local_link, text)
    return _inline_markdown_to_storage(normalized)


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
                html_parts.append('<tr>' + ''.join(f'<th><p>{inline_md_to_storage(c)}</p></th>' for c in header) + '</tr>')
                for row in table_rows[1:]:
                    html_parts.append('<tr>' + ''.join(f'<td><p>{inline_md_to_storage(c)}</p></td>' for c in row) + '</tr>')
                html_parts.append('</tbody></table>')
                table_rows = []
                in_table = False

            if stripped.startswith('- ') or stripped.startswith('* '):
                if not in_list:
                    html_parts.append('<ul>')
                    in_list = True
                item = inline_md_to_storage(stripped[2:])
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
                    p = inline_md_to_storage(stripped)
                    html_parts.append(f'<p>{p}</p>')

        if in_list:
            html_parts.append('</ul>')
        if in_table and table_rows:
            header = table_rows[0]
            html_parts.append('<table data-layout="default"><tbody>')
            html_parts.append('<tr>' + ''.join(f'<th><p>{inline_md_to_storage(c)}</p></th>' for c in header) + '</tr>')
            for row in table_rows[1:]:
                html_parts.append('<tr>' + ''.join(f'<td><p>{inline_md_to_storage(c)}</p></td>' for c in row) + '</tr>')
            html_parts.append('</tbody></table>')

        return '\n'.join(html_parts)

    name_lower = agent['name'].lower()
    if agent.get('diagram'):
        tab_names = get_diagram_tab_names(os.path.join(DIAGRAM_DIR, agent['diagram']))
    else:
        tab_names = []

    html = f'''<h1>{agent['title']}</h1>

<ac:structured-macro ac:name="toc" ac:schema-version="1">
<ac:parameter ac:name="maxLevel">2</ac:parameter>
</ac:structured-macro>

<p><ac:link><ri:page ri:content-title="AI Agent Workforce" /><ac:plain-text-link-body><![CDATA[Back to AI Agent Workforce]]></ac:plain-text-link-body></ac:link></p>

<ac:structured-macro ac:name="info" ac:schema-version="1">
<ac:rich-text-body>
<p><strong>Zone:</strong> {agent['zone']} | <strong>Role:</strong> {agent['role']} | <strong>Wave:</strong> {agent['wave']} | <strong>Sprint:</strong> {agent['sprint']}</p>
</ac:rich-text-body>
</ac:structured-macro>
'''

    for key in sections:
        if key == 'preamble':
            if sections.get(key):
                html += f'\n<h2>Overview</h2>\n{md_section_to_html(sections[key])}'
            continue

        html += f'\n<h2>{key}</h2>\n{md_section_to_html(sections[key])}'

    if tab_names:
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
    plan_path = os.path.join(REPO_ROOT, agent['plan'])

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
    elif resp.status_code in (400, 409):
        print(f"  Page already exists, updating...")
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


USER_DOCS = [
    {'name': 'Drucker', 'title': 'Drucker — User Guide', 'readme': 'agents/drucker/README.md'},
    {'name': 'Gantt', 'title': 'Gantt — User Guide', 'readme': 'agents/gantt/README.md'},
    {'name': 'Hypatia', 'title': 'Hypatia — User Guide', 'readme': 'agents/hypatia/README.md'},
    {'name': 'Shannon', 'title': 'Shannon — User Guide', 'readme': 'agents/shannon/README.md'},
    {'name': 'Workforce', 'title': 'Agent Catalog and Status', 'readme': 'agents/README.md'},
]


def publish_user_doc(c, doc):
    readme_path = os.path.join(REPO_ROOT, doc['readme'])
    if not os.path.exists(readme_path):
        print(f'  SKIP: {readme_path} not found')
        return None

    print(f'\n=== Publishing {doc["title"]} ===')

    with open(readme_path, 'r') as f:
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

    def readme_section_to_html(text):
        html_parts = []
        in_list = False
        in_table = False
        in_code = False
        code_lines = []
        table_rows = []

        for line in text.split('\n'):
            stripped = line.strip()

            if stripped.startswith('```'):
                if in_code:
                    html_parts.append('<ac:structured-macro ac:name="code" ac:schema-version="1">')
                    html_parts.append('<ac:plain-text-body><![CDATA[' + '\n'.join(code_lines) + ']]></ac:plain-text-body>')
                    html_parts.append('</ac:structured-macro>')
                    code_lines = []
                    in_code = False
                else:
                    if in_list:
                        html_parts.append('</ul>')
                        in_list = False
                    in_code = True
                continue
            if in_code:
                code_lines.append(line)
                continue

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
                html_parts.append('<tr>' + ''.join(f'<th><p>{inline_md_to_storage(c)}</p></th>' for c in header) + '</tr>')
                for row in table_rows[1:]:
                    html_parts.append('<tr>' + ''.join(f'<td><p>{inline_md_to_storage(c)}</p></td>' for c in row) + '</tr>')
                html_parts.append('</tbody></table>')
                table_rows = []
                in_table = False

            if stripped.startswith('- ') or stripped.startswith('* '):
                if not in_list:
                    html_parts.append('<ul>')
                    in_list = True
                item = inline_md_to_storage(stripped[2:])
                html_parts.append(f'<li>{item}</li>')
            else:
                if in_list:
                    html_parts.append('</ul>')
                    in_list = False
                if stripped.startswith('### '):
                    html_parts.append(f'<h3>{stripped[4:]}</h3>')
                elif stripped.startswith('#### '):
                    html_parts.append(f'<h4>{stripped[5:]}</h4>')
                elif stripped == '---':
                    html_parts.append('<hr/>')
                elif stripped:
                    p = inline_md_to_storage(stripped)
                    html_parts.append(f'<p>{p}</p>')

        if in_list:
            html_parts.append('</ul>')
        if in_table and table_rows:
            header = table_rows[0]
            html_parts.append('<table data-layout="default"><tbody>')
            html_parts.append('<tr>' + ''.join(f'<th><p>{inline_md_to_storage(c)}</p></th>' for c in header) + '</tr>')
            for row in table_rows[1:]:
                html_parts.append('<tr>' + ''.join(f'<td><p>{inline_md_to_storage(c)}</p></td>' for c in row) + '</tr>')
            html_parts.append('</tbody></table>')
        if in_code and code_lines:
            html_parts.append('<ac:structured-macro ac:name="code" ac:schema-version="1">')
            html_parts.append('<ac:plain-text-body><![CDATA[' + '\n'.join(code_lines) + ']]></ac:plain-text-body>')
            html_parts.append('</ac:structured-macro>')

        return '\n'.join(html_parts)

    html = f'''<h1>{doc['title']}</h1>
<ac:structured-macro ac:name="toc" ac:schema-version="1">
<ac:parameter ac:name="maxLevel">3</ac:parameter>
</ac:structured-macro>
<p><ac:link><ri:page ri:content-title="AI Agent Workforce" /><ac:plain-text-link-body><![CDATA[Back to AI Agent Workforce]]></ac:plain-text-link-body></ac:link></p>
'''

    for key in sections:
        if key == 'preamble':
            if sections.get(key):
                html += f'\n<h2>Overview</h2>\n{readme_section_to_html(sections[key])}'
            continue
        html += f'\n<h2>{key}</h2>\n{readme_section_to_html(sections[key])}'

    payload = {
        'spaceId': SPACE_ID,
        'status': 'current',
        'title': doc['title'],
        'parentId': PARENT_PAGE_ID,
        'body': {'representation': 'storage', 'value': html}
    }

    resp = c.session.post(f'{c.base_url}/api/v2/pages', json=payload)
    if resp.status_code in (200, 201):
        page = resp.json()
        page_id = page['id']
        print(f'  Created page {page_id}')
    elif resp.status_code in (400, 409) and 'already exists' in resp.text.lower():
        print(f'  Page already exists, searching...')
        search_resp = c.session.get(f'{c.base_url}/api/v2/pages', params={
            'spaceId': SPACE_ID, 'title': doc['title'], 'status': 'current'
        })
        results = search_resp.json().get('results', [])
        if results:
            page_id = results[0]['id']
            ver = results[0]['version']['number']
            payload2 = {
                'id': page_id, 'status': 'current', 'title': doc['title'],
                'body': {'representation': 'storage', 'value': html},
                'version': {'number': ver + 1, 'message': 'Updated by publish script'}
            }
            resp2 = c.session.put(f'{c.base_url}/api/v2/pages/{page_id}', json=payload2)
            print(f'  Updated existing page {page_id}: {resp2.status_code}')
        else:
            print(f'  ERROR: Could not find or create page')
            return None
    else:
        print(f'  ERROR creating page: {resp.status_code} {resp.text[:300]}')
        return None

    return page_id


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Publish agent pages to Confluence')
    parser.add_argument('--plans', action='store_true', help='Publish agent plan pages')
    parser.add_argument('--user-docs', action='store_true', help='Publish user documentation (README) pages')
    parser.add_argument('--all', action='store_true', help='Publish everything')
    parser.add_argument('--agent', type=str, help='Publish only this agent (by name)')
    args = parser.parse_args()

    if not args.plans and not args.user_docs and not args.all:
        args.all = True

    c = connect_to_confluence()

    if args.plans or args.all:
        print('\n=== Publishing Agent Plans ===')
        agents = AGENTS
        if args.agent:
            agents = [a for a in AGENTS if a['name'].lower() == args.agent.lower()]
        for agent in agents:
            page_id = publish_agent(c, agent)
            if page_id:
                print(f'  Done: {agent["title"]} -> {page_id}')

    if args.user_docs or args.all:
        print('\n=== Publishing User Documentation ===')
        docs = USER_DOCS
        if args.agent:
            docs = [d for d in USER_DOCS if d['name'].lower() == args.agent.lower()]
        for doc in docs:
            page_id = publish_user_doc(c, doc)
            if page_id:
                print(f'  Done: {doc["title"]} -> {page_id}')

    print('\n=== Done ===')
