#!/usr/bin/env python3
'''Reorder H2 sections in all agents/*/docs/PLAN.md files.

Rule:
  1. Title (H1) preserved
  2. Diagram sections (Diagrams, Use Case Diagram, Sequence Diagram,
     Message Sequence Diagram) move right after Architecture (or Components
     for agents that use that heading)
  3. End sections (Phased roadmap, Implementation Phases, Test and acceptance
     plan, Assumptions) move to the very end, in that order
  4. All other sections keep their original relative order
'''
import os
import re
import glob

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Section names that are "diagram" sections — move right after Architecture
DIAGRAM_NAMES = {
    'diagrams',
    'use case diagram',
    'use case diagrams',
    'message sequence diagram',
    'sequence diagrams',
    'sequence diagram',
}

# Section names that are "end" sections — always last, in this order
END_SECTION_ORDER = [
    'phased roadmap',
    'implementation phases',
    'test and acceptance plan',
    'assumptions',
]

# The anchor section after which diagrams are inserted
ARCHITECTURE_NAMES = {'architecture', 'components'}


def parse_sections(text):
    '''Parse markdown into (title, [(section_name, content), ...]).

    Returns the H1 title line and a list of (name, content) tuples where
    name is the H2 heading text (or '__preamble__' for content before any H2).
    Content includes everything up to (but not including) the next H2/H1.
    '''
    lines = text.split('\n')
    title_line = ''
    sections = []
    current_name = '__preamble__'
    current_lines = []

    for line in lines:
        if line.startswith('# ') and not line.startswith('## '):
            title_line = line
            continue
        if line.startswith('## '):
            # Save previous section
            sections.append((current_name, '\n'.join(current_lines)))
            current_name = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)

    # Save last section
    sections.append((current_name, '\n'.join(current_lines)))

    return title_line, sections


def classify_section(name):
    '''Return 'diagram', 'end', or 'normal'.'''
    lower = name.lower().strip()
    if lower in DIAGRAM_NAMES:
        return 'diagram'
    if lower in [e for e in END_SECTION_ORDER]:
        return 'end'
    return 'normal'


def is_architecture(name):
    return name.lower().strip() in ARCHITECTURE_NAMES


def reorder_sections(sections):
    '''Reorder sections: diagrams after architecture, end sections last.'''
    preamble = None
    normal = []
    diagrams = []
    end_sections = {}

    for name, content in sections:
        if name == '__preamble__':
            preamble = (name, content)
            continue

        kind = classify_section(name)
        if kind == 'diagram':
            diagrams.append((name, content))
        elif kind == 'end':
            end_sections[name.lower().strip()] = (name, content)
        else:
            normal.append((name, content))

    # Find architecture index in normal sections
    arch_idx = None
    for i, (name, _) in enumerate(normal):
        if is_architecture(name):
            arch_idx = i
            break

    # Build result: preamble, then normal sections with diagrams after arch
    result = []
    if preamble:
        result.append(preamble)

    if arch_idx is not None:
        # Normal sections up to and including Architecture
        result.extend(normal[:arch_idx + 1])
        # Insert diagram sections
        result.extend(diagrams)
        # Remaining normal sections
        result.extend(normal[arch_idx + 1:])
    else:
        # No architecture section found — put diagrams after all normal
        result.extend(normal)
        result.extend(diagrams)

    # Append end sections in canonical order
    for end_name in END_SECTION_ORDER:
        if end_name in end_sections:
            result.append(end_sections[end_name])

    return result


def rebuild_markdown(title_line, sections):
    '''Reconstruct markdown from title and sections.'''
    parts = []
    if title_line:
        parts.append(title_line)

    for name, content in sections:
        if name == '__preamble__':
            if content.strip():
                parts.append(content)
        else:
            parts.append(f'\n## {name}')
            parts.append(content)

    text = '\n'.join(parts)
    # Normalize: no more than 2 consecutive blank lines
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    # Ensure file ends with single newline
    text = text.rstrip('\n') + '\n'
    return text


def process_file(filepath, dry_run=False):
    '''Reorder sections in a single PLAN.md file.'''
    with open(filepath, 'r') as f:
        original = f.read()

    # Skip YAML frontmatter (Brandeis has it)
    frontmatter = ''
    body = original
    if original.startswith('---'):
        end = original.find('---', 3)
        if end != -1:
            frontmatter = original[:end + 3] + '\n'
            body = original[end + 3:]

    title_line, sections = parse_sections(body)
    reordered = reorder_sections(sections)
    new_body = rebuild_markdown(title_line, reordered)
    new_content = frontmatter + new_body

    if new_content == original:
        return False  # No changes needed

    if not dry_run:
        with open(filepath, 'w') as f:
            f.write(new_content)

    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Reorder PLAN.md sections')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would change without writing')
    args = parser.parse_args()

    plan_files = sorted(glob.glob(
        os.path.join(REPO_ROOT, 'agents', '*', 'docs', 'PLAN.md')
    ))

    changed = 0
    for filepath in plan_files:
        agent = filepath.split(os.sep)[-3]
        modified = process_file(filepath, dry_run=args.dry_run)
        status = 'CHANGED' if modified else 'ok'
        print(f'  {agent:15s} {status}')
        if modified:
            changed += 1

    action = 'Would change' if args.dry_run else 'Changed'
    print(f'\n{action} {changed}/{len(plan_files)} files')


if __name__ == '__main__':
    main()
