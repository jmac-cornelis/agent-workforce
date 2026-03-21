##########################################################################################
#
# Module: tests/test_markdown_to_confluence.py
#
# Description: Tests for the enhanced markdown_to_storage() converter, diagram rendering,
#              convert_markdown_to_confluence() pipeline, and the agent-callable tool.
#
# Author: Cornelis Networks
#
##########################################################################################

import html
import os
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

import confluence_utils
from confluence_utils import (
    DiagramRenderResult,
    _get_drawio_tab_names,
    convert_markdown_to_confluence,
    load_markdown_document,
    markdown_to_storage,
    render_diagrams,
)


# ---------------------------------------------------------------------------
# markdown_to_storage — inline constructs
# ---------------------------------------------------------------------------

class TestInlineMarkdown:
    '''Tests for inline Markdown constructs inside paragraphs.'''

    def test_bold_double_asterisk(self):
        result = markdown_to_storage('**bold text**')
        assert '<strong>bold text</strong>' in result

    def test_bold_double_underscore(self):
        result = markdown_to_storage('__bold text__')
        assert '<strong>bold text</strong>' in result

    def test_italic_single_asterisk(self):
        result = markdown_to_storage('*italic text*')
        assert '<em>italic text</em>' in result

    def test_italic_single_underscore(self):
        result = markdown_to_storage('_italic text_')
        assert '<em>italic text</em>' in result

    def test_strikethrough(self):
        result = markdown_to_storage('~~deleted text~~')
        assert '<del>deleted text</del>' in result

    def test_inline_code(self):
        result = markdown_to_storage('Use `git status` to check')
        assert '<code>git status</code>' in result

    def test_link(self):
        result = markdown_to_storage('[Example](https://example.com)')
        assert '<a href="https://example.com">Example</a>' in result

    def test_inline_image_remote(self):
        result = markdown_to_storage('![logo](https://example.com/logo.png)')
        assert 'ac:image' in result
        assert 'ri:url' in result
        assert 'https://example.com/logo.png' in result

    def test_inline_image_local(self):
        result = markdown_to_storage('![diagram](images/arch.png)')
        assert 'ac:image' in result
        assert 'ri:attachment' in result
        assert 'arch.png' in result

    def test_mixed_inline(self):
        result = markdown_to_storage('**bold** and *italic* and `code`')
        assert '<strong>bold</strong>' in result
        assert '<em>italic</em>' in result
        assert '<code>code</code>' in result


# ---------------------------------------------------------------------------
# markdown_to_storage — block constructs
# ---------------------------------------------------------------------------

class TestBlockMarkdown:
    '''Tests for block-level Markdown constructs.'''

    def test_headings_h1_through_h6(self):
        for level in range(1, 7):
            hashes = '#' * level
            result = markdown_to_storage(f'{hashes} Heading {level}')
            assert f'<h{level}>Heading {level}</h{level}>' in result

    def test_paragraph(self):
        result = markdown_to_storage('Hello world')
        assert '<p>Hello world</p>' in result

    def test_multiple_paragraphs(self):
        result = markdown_to_storage('First paragraph\n\nSecond paragraph')
        assert '<p>First paragraph</p>' in result
        assert '<p>Second paragraph</p>' in result

    def test_fenced_code_block(self):
        md = '```python\nprint("hello")\n```'
        result = markdown_to_storage(md)
        assert 'ac:structured-macro ac:name="code"' in result
        assert 'language' in result
        assert 'python' in result
        assert 'print("hello")' in result

    def test_fenced_code_block_no_language(self):
        md = '```\nsome code\n```'
        result = markdown_to_storage(md)
        assert 'ac:structured-macro ac:name="code"' in result
        assert 'some code' in result

    def test_horizontal_rule_dashes(self):
        result = markdown_to_storage('---')
        assert '<hr />' in result

    def test_horizontal_rule_asterisks(self):
        result = markdown_to_storage('***')
        assert '<hr />' in result

    def test_horizontal_rule_underscores(self):
        result = markdown_to_storage('___')
        assert '<hr />' in result


# ---------------------------------------------------------------------------
# markdown_to_storage — lists
# ---------------------------------------------------------------------------

class TestLists:
    '''Tests for list constructs.'''

    def test_unordered_list_dash(self):
        md = '- Item one\n- Item two\n- Item three'
        result = markdown_to_storage(md)
        assert '<ul>' in result
        assert '<li>Item one</li>' in result
        assert '<li>Item two</li>' in result
        assert '<li>Item three</li>' in result
        assert '</ul>' in result

    def test_unordered_list_asterisk(self):
        md = '* Alpha\n* Beta'
        result = markdown_to_storage(md)
        assert '<ul>' in result
        assert '<li>Alpha</li>' in result

    def test_unordered_list_plus(self):
        md = '+ First\n+ Second'
        result = markdown_to_storage(md)
        assert '<ul>' in result
        assert '<li>First</li>' in result

    def test_ordered_list(self):
        md = '1. First\n2. Second\n3. Third'
        result = markdown_to_storage(md)
        assert '<ol>' in result
        assert '<li>First</li>' in result
        assert '<li>Second</li>' in result
        assert '</ol>' in result

    def test_nested_unordered_list(self):
        md = '- Parent\n  - Child\n  - Child 2\n- Parent 2'
        result = markdown_to_storage(md)
        assert '<ul>' in result
        # Nested list should be inside a parent <li>
        assert '<li>Parent' in result
        assert '<li>Child</li>' in result
        assert '<li>Parent 2</li>' in result

    def test_task_list_incomplete(self):
        md = '- [ ] Todo item'
        result = markdown_to_storage(md)
        assert 'ac:task-list' in result
        assert 'ac:task-body' in result
        assert 'incomplete' in result

    def test_task_list_complete(self):
        md = '- [x] Done item'
        result = markdown_to_storage(md)
        assert 'ac:task-list' in result
        assert 'complete' in result

    def test_task_list_mixed(self):
        md = '- [x] Done\n- [ ] Not done'
        result = markdown_to_storage(md)
        assert 'ac:task-list' in result
        assert result.count('ac:task>') >= 2  # opening + closing for each


# ---------------------------------------------------------------------------
# markdown_to_storage — tables
# ---------------------------------------------------------------------------

class TestTables:
    '''Tests for pipe table constructs.'''

    def test_simple_table(self):
        md = '| Name | Value |\n| --- | --- |\n| A | 1 |\n| B | 2 |'
        result = markdown_to_storage(md)
        assert '<table' in result
        assert '<th>' in result
        assert '<td>' in result
        assert 'Name' in result
        assert 'Value' in result

    def test_table_with_inline_formatting(self):
        md = '| Col |\n| --- |\n| **bold** |'
        result = markdown_to_storage(md)
        assert '<strong>bold</strong>' in result


# ---------------------------------------------------------------------------
# markdown_to_storage — blockquotes
# ---------------------------------------------------------------------------

class TestBlockquotes:
    '''Tests for blockquote constructs.'''

    def test_simple_blockquote(self):
        md = '> This is a quote'
        result = markdown_to_storage(md)
        assert '<blockquote>' in result
        assert 'This is a quote' in result
        assert '</blockquote>' in result

    def test_multiline_blockquote(self):
        md = '> Line one\n> Line two'
        result = markdown_to_storage(md)
        assert '<blockquote>' in result
        assert 'Line one' in result
        assert 'Line two' in result

    def test_blockquote_with_inline_formatting(self):
        md = '> **Bold** in a quote'
        result = markdown_to_storage(md)
        assert '<blockquote>' in result
        assert '<strong>Bold</strong>' in result


# ---------------------------------------------------------------------------
# markdown_to_storage — GitHub admonitions
# ---------------------------------------------------------------------------

class TestAdmonitions:
    '''Tests for GitHub-style admonitions.'''

    def test_note_admonition(self):
        md = '> [!NOTE]\n> This is a note.'
        result = markdown_to_storage(md)
        assert 'ac:structured-macro ac:name="info"' in result
        assert 'This is a note.' in result

    def test_tip_admonition(self):
        md = '> [!TIP]\n> Helpful tip here.'
        result = markdown_to_storage(md)
        assert 'ac:structured-macro ac:name="tip"' in result
        assert 'Helpful tip here.' in result

    def test_warning_admonition(self):
        md = '> [!WARNING]\n> Be careful!'
        result = markdown_to_storage(md)
        assert 'ac:structured-macro ac:name="warning"' in result
        assert 'Be careful!' in result

    def test_important_admonition(self):
        md = '> [!IMPORTANT]\n> Critical info.'
        result = markdown_to_storage(md)
        assert 'ac:structured-macro ac:name="note"' in result
        assert 'Critical info.' in result

    def test_caution_admonition(self):
        md = '> [!CAUTION]\n> Danger zone.'
        result = markdown_to_storage(md)
        assert 'ac:structured-macro ac:name="warning"' in result
        assert 'Danger zone.' in result

    def test_admonition_with_multiline_body(self):
        md = '> [!NOTE]\n> Line one.\n> Line two.'
        result = markdown_to_storage(md)
        assert 'ac:structured-macro ac:name="info"' in result
        assert 'Line one.' in result
        assert 'Line two.' in result


# ---------------------------------------------------------------------------
# markdown_to_storage — standalone images
# ---------------------------------------------------------------------------

class TestStandaloneImages:
    '''Tests for standalone image lines.'''

    def test_standalone_remote_image(self):
        md = '![Architecture](https://example.com/arch.png)'
        result = markdown_to_storage(md)
        assert '<p><ac:image' in result
        assert 'ri:url' in result
        assert 'https://example.com/arch.png' in result

    def test_standalone_local_image(self):
        md = '![Diagram](diagrams/flow.png)'
        result = markdown_to_storage(md)
        assert '<p><ac:image' in result
        assert 'ri:attachment' in result
        assert 'flow.png' in result


# ---------------------------------------------------------------------------
# markdown_to_storage — comprehensive document
# ---------------------------------------------------------------------------

class TestComprehensiveDocument:
    '''Test a realistic multi-construct Markdown document.'''

    def test_full_document(self):
        md = textwrap.dedent('''\
            # Release Notes

            ## Overview

            This release includes **important** changes.

            > [!WARNING]
            > Breaking changes ahead.

            ## Changes

            | Feature | Status |
            | --- | --- |
            | Auth | Done |
            | API | In Progress |

            ### Task List

            - [x] Implement auth
            - [ ] Write tests
            - [ ] Deploy

            ### Code Example

            ```python
            def hello():
                print("world")
            ```

            ---

            > This is a regular blockquote.

            1. First step
            2. Second step
               - Sub-item A
               - Sub-item B

            ![logo](https://example.com/logo.png)
        ''')
        result = markdown_to_storage(md)

        # Headings
        assert '<h1>Release Notes</h1>' in result
        assert '<h2>Overview</h2>' in result
        assert '<h2>Changes</h2>' in result
        assert '<h3>Task List</h3>' in result
        assert '<h3>Code Example</h3>' in result

        # Inline
        assert '<strong>important</strong>' in result

        # Admonition
        assert 'ac:structured-macro ac:name="warning"' in result
        assert 'Breaking changes ahead.' in result

        # Table
        assert '<table' in result
        assert '<th>' in result

        # Task list
        assert 'ac:task-list' in result

        # Code block
        assert 'ac:structured-macro ac:name="code"' in result
        assert 'print("world")' in result

        # Horizontal rule
        assert '<hr />' in result

        # Blockquote
        assert '<blockquote>' in result

        # Ordered list
        assert '<ol>' in result

        # Image
        assert 'ac:image' in result


# ---------------------------------------------------------------------------
# render_diagrams
# ---------------------------------------------------------------------------

class TestRenderDiagrams:
    '''Tests for the render_diagrams() function.'''

    def test_no_diagrams_returns_unchanged(self):
        md = '# Hello\n\nNo diagrams here.'
        result = render_diagrams(md)
        assert result.markdown == md
        assert result.rendered_count == 0
        assert result.attachments == []
        assert result.errors == []

    def test_non_diagram_code_block_preserved(self):
        md = '```python\nprint("hello")\n```'
        result = render_diagrams(md)
        assert '```python' in result.markdown
        assert 'print("hello")' in result.markdown
        assert result.rendered_count == 0

    def test_mermaid_block_detected(self, tmp_path):
        '''Verify mermaid blocks are detected and render is attempted.'''
        md = '```mermaid\ngraph TD\n  A --> B\n```'

        # Mock _render_mermaid to create a fake PNG
        def fake_render(source, output_path):
            output_path.write_bytes(b'fake-png')

        with patch('confluence_utils._render_mermaid', side_effect=fake_render):
            result = render_diagrams(md, output_dir=str(tmp_path))

        assert result.rendered_count == 1
        assert len(result.attachments) == 1
        assert result.attachments[0]['filename'].startswith('diagram_mermaid_')
        assert result.attachments[0]['filename'].endswith('.png')
        assert '![mermaid diagram]' in result.markdown
        assert '```mermaid' not in result.markdown

    def test_mermaid_render_failure_preserves_block(self, tmp_path):
        '''When rendering fails, the original fenced block is preserved.'''
        md = '```mermaid\ninvalid diagram\n```'

        def failing_render(source, output_path):
            raise RuntimeError('render failed')

        with patch('confluence_utils._render_mermaid', side_effect=failing_render):
            result = render_diagrams(md, output_dir=str(tmp_path))

        assert result.rendered_count == 0
        assert len(result.errors) == 1
        assert 'render failed' in result.errors[0]
        assert '```mermaid' in result.markdown
        assert 'invalid diagram' in result.markdown

    def test_multiple_diagrams(self, tmp_path):
        '''Multiple mermaid blocks are each rendered independently.'''
        md = (
            '```mermaid\ngraph TD\n  A --> B\n```\n\n'
            'Some text\n\n'
            '```mermaid\nsequenceDiagram\n  A->>B: Hello\n```'
        )

        def fake_render(source, output_path):
            output_path.write_bytes(b'fake-png')

        with patch('confluence_utils._render_mermaid', side_effect=fake_render):
            result = render_diagrams(md, output_dir=str(tmp_path))

        assert result.rendered_count == 2
        assert len(result.attachments) == 2
        assert 'Some text' in result.markdown

    def test_mixed_diagram_and_code(self, tmp_path):
        '''Mermaid blocks are rendered but python blocks are preserved.'''
        md = (
            '```python\nprint("hi")\n```\n\n'
            '```mermaid\ngraph TD\n  A --> B\n```'
        )

        def fake_render(source, output_path):
            output_path.write_bytes(b'fake-png')

        with patch('confluence_utils._render_mermaid', side_effect=fake_render):
            result = render_diagrams(md, output_dir=str(tmp_path))

        assert result.rendered_count == 1
        assert '```python' in result.markdown
        assert 'print("hi")' in result.markdown
        assert '```mermaid' not in result.markdown


# ---------------------------------------------------------------------------
# _find_mmdc / _render_mermaid
# ---------------------------------------------------------------------------

class TestMermaidHelpers:
    '''Tests for mermaid rendering helpers.'''

    def test_find_mmdc_returns_path_or_none(self):
        result = confluence_utils._find_mmdc()
        # On CI or systems without mmdc, this may be None
        assert result is None or os.path.isfile(result)

    def test_render_mermaid_raises_without_mmdc(self, tmp_path):
        '''When mmdc is not on PATH, _render_mermaid raises RuntimeError.'''
        with patch('confluence_utils._find_mmdc', return_value=None):
            with pytest.raises(RuntimeError, match='mmdc.*not found'):
                confluence_utils._render_mermaid(
                    'graph TD\n  A --> B',
                    tmp_path / 'out.png',
                )


# ---------------------------------------------------------------------------
# convert_markdown_to_confluence (full pipeline)
# ---------------------------------------------------------------------------

class TestConvertMarkdownToConfluence:
    '''Tests for the full conversion pipeline.'''

    def test_simple_markdown_no_diagrams(self):
        result = convert_markdown_to_confluence(
            '# Hello\n\nWorld',
            render_diagrams_flag=False,
        )
        assert '<h1>Hello</h1>' in result['storage']
        assert '<p>World</p>' in result['storage']
        assert result['diagrams_rendered'] == 0
        assert result['attachments'] == []

    def test_with_diagrams_enabled(self, tmp_path):
        md = '# Doc\n\n```mermaid\ngraph TD\n  A --> B\n```'

        def fake_render(source, output_path):
            output_path.write_bytes(b'fake-png')

        with patch('confluence_utils._render_mermaid', side_effect=fake_render):
            result = convert_markdown_to_confluence(
                md,
                render_diagrams_flag=True,
                output_dir=str(tmp_path),
            )

        assert '<h1>Doc</h1>' in result['storage']
        assert result['diagrams_rendered'] == 1
        assert len(result['attachments']) == 1
        # The rendered image should appear as an ac:image in storage
        assert 'ac:image' in result['storage']

    def test_with_diagrams_disabled(self):
        md = '```mermaid\ngraph TD\n  A --> B\n```'
        result = convert_markdown_to_confluence(
            md,
            render_diagrams_flag=False,
        )
        # Mermaid block should be rendered as a code block, not an image
        assert 'ac:structured-macro ac:name="code"' in result['storage']
        assert result['diagrams_rendered'] == 0

    def test_returns_diagram_errors(self, tmp_path):
        md = '```mermaid\nbad diagram\n```'

        def failing_render(source, output_path):
            raise RuntimeError('render failed')

        with patch('confluence_utils._render_mermaid', side_effect=failing_render):
            result = convert_markdown_to_confluence(
                md,
                render_diagrams_flag=True,
                output_dir=str(tmp_path),
            )

        assert result['diagrams_rendered'] == 0
        assert len(result['diagram_errors']) == 1
        assert 'render failed' in result['diagram_errors'][0]


# ---------------------------------------------------------------------------
# DiagramRenderResult dataclass
# ---------------------------------------------------------------------------

class TestDiagramRenderResult:
    '''Tests for the DiagramRenderResult dataclass.'''

    def test_defaults(self):
        r = DiagramRenderResult(markdown='# Hello')
        assert r.markdown == '# Hello'
        assert r.attachments == []
        assert r.rendered_count == 0
        assert r.errors == []

    def test_with_values(self):
        r = DiagramRenderResult(
            markdown='![img](out.png)',
            attachments=[{'source_path': '/tmp/out.png', 'filename': 'out.png'}],
            rendered_count=1,
            errors=[],
        )
        assert r.rendered_count == 1
        assert len(r.attachments) == 1


# ---------------------------------------------------------------------------
# Tool wrapper: convert_markdown_to_confluence
# ---------------------------------------------------------------------------

class TestConvertMarkdownTool:
    '''Tests for the agent-callable tool wrapper.'''

    def test_tool_returns_success(self, monkeypatch):
        from tools import confluence_tools

        monkeypatch.setattr(
            confluence_tools,
            '_cu_convert_markdown',
            lambda markdown_text, render_diagrams_flag=True, output_dir=None: {
                'storage': '<p>Hello</p>',
                'attachments': [],
                'diagrams_rendered': 0,
                'diagram_errors': [],
            },
        )

        result = confluence_tools.convert_markdown_to_confluence('Hello')
        assert result.is_success
        assert '<p>Hello</p>' in result.data['storage']

    def test_tool_returns_failure_on_error(self, monkeypatch):
        from tools import confluence_tools

        def failing_convert(markdown_text, render_diagrams_flag=True, output_dir=None):
            raise RuntimeError('conversion failed')

        monkeypatch.setattr(
            confluence_tools,
            '_cu_convert_markdown',
            failing_convert,
        )

        result = confluence_tools.convert_markdown_to_confluence('bad input')
        assert not result.is_success
        assert 'conversion failed' in result.error

    def test_tool_registered_in_collection(self):
        from tools.confluence_tools import ConfluenceTools
        tools = ConfluenceTools()
        assert tools.get_tool('convert_markdown_to_confluence') is not None


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    '''Edge case tests for the converter.'''

    def test_empty_string(self):
        result = markdown_to_storage('')
        assert result == '<p></p>'

    def test_only_whitespace(self):
        result = markdown_to_storage('   \n\n   ')
        assert result == '<p></p>'

    def test_html_entities_escaped(self):
        # Raw HTML angle brackets and ampersands should be escaped in output
        result = markdown_to_storage("Use <div> and &")
        # The converter escapes HTML entities
        assert "&lt;div&gt;" in result
        assert "&amp;" in result

    def test_extra_fragments_passed_through(self):
        fragments = {'@@TOKEN@@': '<ac:link>custom</ac:link>'}
        result = markdown_to_storage('See @@TOKEN@@ here', extra_fragments=fragments)
        assert '<ac:link>custom</ac:link>' in result

    def test_html_block_table_passthrough(self):
        '''Raw HTML <table> blocks should pass through unchanged.'''
        md = (
            'Before\n\n'
            '<table>\n<tr><th>A</th></tr>\n<tr><td>1</td></tr>\n</table>\n\n'
            'After'
        )
        result = markdown_to_storage(md)
        assert '<table>' in result
        assert '<tr><th>A</th></tr>' in result
        assert '</table>' in result
        # Surrounding text should still be wrapped in <p>
        assert '<p>Before</p>' in result
        assert '<p>After</p>' in result

    def test_html_block_nested_tables(self):
        '''Nested HTML tables should be collected as a single block.'''
        md = (
            '<table>\n<tr><td>\n<table><tr><td>inner</td></tr></table>\n'
            '</td></tr>\n</table>'
        )
        result = markdown_to_storage(md)
        assert result.count('<table>') == 2
        assert result.count('</table>') == 2
        assert 'inner' in result

    def test_html_block_div_passthrough(self):
        '''Raw HTML <div> blocks should pass through unchanged.'''
        md = '<div class="note">\nHello world\n</div>'
        result = markdown_to_storage(md)
        assert '<div class="note">' in result
        assert '</div>' in result

    def test_html_block_inline_markdown_bold(self):
        '''**bold** inside HTML table cells should become <strong>.'''
        md = '<table>\n<tr><td>**Josephine** — Build</td></tr>\n</table>'
        result = markdown_to_storage(md)
        assert '<strong>Josephine</strong>' in result
        # HTML structure should be preserved
        assert '<table>' in result
        assert '</table>' in result

    def test_html_block_inline_markdown_italic(self):
        '''*italic* inside HTML blocks should become <em>.'''
        md = '<div>\n*emphasis here*\n</div>'
        result = markdown_to_storage(md)
        assert '<em>emphasis here</em>' in result

    def test_html_block_inline_markdown_strikethrough(self):
        '''~~strikethrough~~ inside HTML blocks should become <del>.'''
        md = '<table>\n<tr><td>~~removed~~</td></tr>\n</table>'
        result = markdown_to_storage(md)
        assert '<del>removed</del>' in result

    def test_html_block_inline_markdown_preserves_attributes(self):
        '''Inline markdown conversion must not alter HTML tag attributes.'''
        md = (
            '<table>\n'
            '<th style="background:#dae8fc;text-align:center">**Header**</th>\n'
            '</table>'
        )
        result = markdown_to_storage(md)
        assert 'style="background:#dae8fc;text-align:center"' in result
        assert '<strong>Header</strong>' in result


# ---------------------------------------------------------------------------
# load_markdown_document — diagram rendering integration
# ---------------------------------------------------------------------------

class TestLoadMarkdownDocumentDiagrams:
    '''Tests that load_markdown_document() renders diagrams to attachments.'''

    def test_mermaid_diagram_rendered_to_attachment(self, tmp_path):
        '''A mermaid fenced block in a .md file should be rendered to a PNG
        attachment and replaced with an <ac:image> tag in body_storage.'''
        md_file = tmp_path / 'page.md'
        md_file.write_text(
            '---\ntitle: Test\n---\n\n'
            '# Architecture\n\n'
            '```mermaid\n'
            'graph TD\n'
            '    A[Start] --> B[End]\n'
            '```\n\n'
            'After the diagram.\n',
            encoding='utf-8',
        )

        # Mock _render_mermaid so we don't need mmdc installed in CI
        def fake_render(source, output_path):
            output_path.write_bytes(b'FAKEPNG')

        with patch('confluence_utils._render_mermaid', side_effect=fake_render):
            doc = load_markdown_document(str(md_file))

        # The diagram should appear as an <ac:image> attachment reference
        assert 'ri:attachment ri:filename="diagram_mermaid_' in doc.body_storage
        assert 'ac:image' in doc.body_storage
        # The original mermaid code block should NOT appear
        assert 'graph TD' not in doc.body_storage
        assert 'ac:name="code"' not in doc.body_storage or 'mermaid' not in doc.body_storage

        # There should be a PNG attachment in the attachments list
        diagram_attachments = [
            a for a in doc.attachments if a['filename'].startswith('diagram_mermaid_')
        ]
        assert len(diagram_attachments) == 1
        assert diagram_attachments[0]['filename'].endswith('.png')

    def test_diagram_rendering_disabled(self, tmp_path):
        '''When render_diagrams_flag=False, mermaid blocks stay as code blocks.'''
        md_file = tmp_path / 'page.md'
        md_file.write_text(
            '---\ntitle: Test\n---\n\n'
            '```mermaid\n'
            'graph TD\n'
            '    A --> B\n'
            '```\n',
            encoding='utf-8',
        )

        doc = load_markdown_document(str(md_file), render_diagrams_flag=False)

        # Should be a code block, not an image
        assert 'ac:name="code"' in doc.body_storage
        # No diagram attachments
        diagram_attachments = [
            a for a in doc.attachments if a['filename'].startswith('diagram_mermaid_')
        ]
        assert len(diagram_attachments) == 0

    def test_diagram_render_failure_preserves_code_block(self, tmp_path):
        '''When mmdc fails, the mermaid block should remain as a code block.'''
        md_file = tmp_path / 'page.md'
        md_file.write_text(
            '---\ntitle: Test\n---\n\n'
            '```mermaid\n'
            'invalid diagram syntax\n'
            '```\n',
            encoding='utf-8',
        )

        def failing_render(source, output_path):
            raise RuntimeError('mmdc failed')

        with patch('confluence_utils._render_mermaid', side_effect=failing_render):
            doc = load_markdown_document(str(md_file))

        # Should fall back to a code block
        assert 'ac:name="code"' in doc.body_storage
        # No diagram attachments
        diagram_attachments = [
            a for a in doc.attachments if a['filename'].startswith('diagram_mermaid_')
        ]
        assert len(diagram_attachments) == 0

    def test_mixed_diagrams_and_images(self, tmp_path):
        '''A file with both a mermaid diagram and a regular image should
        produce attachments for both.'''
        img_file = tmp_path / 'photo.png'
        img_file.write_bytes(b'PNG')

        md_file = tmp_path / 'page.md'
        md_file.write_text(
            '---\ntitle: Mixed\n---\n\n'
            '![Photo](photo.png)\n\n'
            '```mermaid\n'
            'graph LR\n'
            '    X --> Y\n'
            '```\n',
            encoding='utf-8',
        )

        def fake_render(source, output_path):
            output_path.write_bytes(b'FAKEPNG')

        with patch('confluence_utils._render_mermaid', side_effect=fake_render):
            doc = load_markdown_document(str(md_file))

        filenames = {a['filename'] for a in doc.attachments}
        # Should have the regular image attachment
        assert 'photo.png' in filenames
        # Should have the rendered diagram attachment
        diagram_filenames = [f for f in filenames if f.startswith('diagram_mermaid_')]
        assert len(diagram_filenames) == 1

        # Both should appear as <ac:image> in the storage
        assert 'ri:attachment ri:filename="photo.png"' in doc.body_storage
        assert 'ri:attachment ri:filename="diagram_mermaid_' in doc.body_storage

    def test_multiple_mermaid_diagrams(self, tmp_path):
        '''Multiple mermaid blocks should each produce a separate attachment.'''
        md_file = tmp_path / 'page.md'
        md_file.write_text(
            '---\ntitle: Multi\n---\n\n'
            '```mermaid\n'
            'graph TD\n'
            '    A --> B\n'
            '```\n\n'
            '```mermaid\n'
            'sequenceDiagram\n'
            '    Alice->>Bob: Hello\n'
            '```\n',
            encoding='utf-8',
        )

        def fake_render(source, output_path):
            output_path.write_bytes(b'FAKEPNG')

        with patch('confluence_utils._render_mermaid', side_effect=fake_render):
            doc = load_markdown_document(str(md_file))

        diagram_attachments = [
            a for a in doc.attachments if a['filename'].startswith('diagram_mermaid_')
        ]
        # Two different diagrams → two different content hashes → two attachments
        assert len(diagram_attachments) == 2
        assert diagram_attachments[0]['filename'] != diagram_attachments[1]['filename']


# ---------------------------------------------------------------------------
# Draw.io helpers
# ---------------------------------------------------------------------------

class TestDrawioHelpers:
    '''Tests for draw.io rendering helper functions.'''

    def test_find_drawio_returns_path_or_none(self):
        '''_find_drawio should return a string path or None.'''
        result = confluence_utils._find_drawio()
        assert result is None or isinstance(result, str)

    def test_get_drawio_tab_names_from_valid_xml(self, tmp_path):
        '''_get_drawio_tab_names should extract tab names from a .drawio file.'''
        drawio_file = tmp_path / 'test.drawio'
        drawio_file.write_text(
            '<mxfile>'
            '<diagram id="d1" name="Tab One"><mxGraphModel/></diagram>'
            '<diagram id="d2" name="Tab Two"><mxGraphModel/></diagram>'
            '</mxfile>',
            encoding='utf-8',
        )
        names = _get_drawio_tab_names(str(drawio_file))
        assert names == ['Tab One', 'Tab Two']

    def test_get_drawio_tab_names_fallback_regex(self, tmp_path):
        '''When XML parsing fails, _get_drawio_tab_names falls back to regex.'''
        drawio_file = tmp_path / 'test.drawio'
        # Include an HTML entity that breaks strict XML parsing
        drawio_file.write_text(
            '<mxfile>'
            '<diagram id="d1" name="First Tab">'
            '<mxGraphModel><root>'
            '<mxCell id="0" value="A&#xa;B"/>'
            '</root></mxGraphModel></diagram>'
            '</mxfile>',
            encoding='utf-8',
        )
        names = _get_drawio_tab_names(str(drawio_file))
        assert names == ['First Tab']

    def test_get_drawio_tab_names_missing_file(self, tmp_path):
        '''Missing file returns empty list.'''
        names = _get_drawio_tab_names(str(tmp_path / 'nonexistent.drawio'))
        assert names == []

    def test_render_drawio_raises_without_cli(self, tmp_path):
        '''When drawio CLI is not on PATH, _render_drawio raises RuntimeError.'''
        drawio_file = tmp_path / 'test.drawio'
        drawio_file.write_text(
            '<mxfile><diagram id="d1" name="Page 1">'
            '<mxGraphModel/></diagram></mxfile>',
            encoding='utf-8',
        )
        with patch('confluence_utils._find_drawio', return_value=None):
            with pytest.raises(RuntimeError, match='drawio CLI.*not found'):
                confluence_utils._render_drawio(
                    str(drawio_file), tmp_path, 'test_diagram',
                )


# ---------------------------------------------------------------------------
# render_diagrams — draw.io image references
# ---------------------------------------------------------------------------

class TestRenderDiagramsDrawio:
    '''Tests for draw.io image reference handling in render_diagrams().'''

    def test_drawio_image_detected_and_rendered(self, tmp_path):
        '''A ![alt](file.drawio) line should be detected and rendered.'''
        drawio_file = tmp_path / 'arch.drawio'
        drawio_file.write_text(
            '<mxfile>'
            '<diagram id="d1" name="Overview"><mxGraphModel/></diagram>'
            '</mxfile>',
            encoding='utf-8',
        )
        md = f'# Title\n\n![Architecture]({drawio_file.name})\n\nAfter.'

        def fake_render(drawio_path, output_dir, base_name):
            png = output_dir / f'{base_name}_tab1.png'
            png.write_bytes(b'FAKEPNG')
            return [{'source_path': str(png), 'filename': png.name, 'tab_name': 'Overview'}]

        with patch('confluence_utils._render_drawio', side_effect=fake_render):
            result = render_diagrams(md, output_dir=str(tmp_path), base_dir=tmp_path)

        assert result.rendered_count == 1
        assert len(result.attachments) == 1
        assert result.attachments[0]['filename'].endswith('.png')
        assert 'arch.drawio' not in result.markdown
        assert '![Overview]' in result.markdown
        assert 'After.' in result.markdown

    def test_drawio_multi_tab_produces_multiple_images(self, tmp_path):
        '''A multi-tab .drawio file should produce one image per tab.'''
        drawio_file = tmp_path / 'multi.drawio'
        drawio_file.write_text(
            '<mxfile>'
            '<diagram id="d1" name="Tab A"><mxGraphModel/></diagram>'
            '<diagram id="d2" name="Tab B"><mxGraphModel/></diagram>'
            '</mxfile>',
            encoding='utf-8',
        )
        md = f'![Diagram]({drawio_file.name})'

        def fake_render(drawio_path, output_dir, base_name):
            results = []
            for i, name in enumerate(['Tab A', 'Tab B'], 1):
                png = output_dir / f'{base_name}_tab{i}.png'
                png.write_bytes(b'FAKEPNG')
                results.append({
                    'source_path': str(png),
                    'filename': png.name,
                    'tab_name': name,
                })
            return results

        with patch('confluence_utils._render_drawio', side_effect=fake_render):
            result = render_diagrams(md, output_dir=str(tmp_path), base_dir=tmp_path)

        assert result.rendered_count == 2
        assert len(result.attachments) == 2
        assert '![Tab A]' in result.markdown
        assert '![Tab B]' in result.markdown

    def test_drawio_missing_file_produces_error(self, tmp_path):
        '''A reference to a non-existent .drawio file should produce an error.'''
        md = '![Missing](nonexistent.drawio)'
        result = render_diagrams(md, output_dir=str(tmp_path), base_dir=tmp_path)
        assert result.rendered_count == 0
        assert len(result.errors) == 1
        assert 'not found' in result.errors[0]
        # Original line preserved
        assert '![Missing](nonexistent.drawio)' in result.markdown

    def test_drawio_render_failure_preserves_line(self, tmp_path):
        '''When drawio CLI fails, the original image line is preserved.'''
        drawio_file = tmp_path / 'broken.drawio'
        drawio_file.write_text(
            '<mxfile><diagram id="d1" name="P1"><mxGraphModel/></diagram></mxfile>',
            encoding='utf-8',
        )
        md = f'![Broken]({drawio_file.name})'

        def failing_render(drawio_path, output_dir, base_name):
            raise RuntimeError('drawio export failed')

        with patch('confluence_utils._render_drawio', side_effect=failing_render):
            result = render_diagrams(md, output_dir=str(tmp_path), base_dir=tmp_path)

        assert result.rendered_count == 0
        assert len(result.errors) == 1
        assert 'drawio export failed' in result.errors[0]
        assert f'![Broken]({drawio_file.name})' in result.markdown

    def test_drawio_not_matched_when_not_standalone(self, tmp_path):
        '''A .drawio reference inside a paragraph should NOT be matched.'''
        md = 'See the diagram at ![arch](arch.drawio) for details.'
        result = render_diagrams(md, output_dir=str(tmp_path), base_dir=tmp_path)
        # The regex requires the image to be the only thing on the line
        assert result.rendered_count == 0
        assert 'arch.drawio' in result.markdown

    def test_mixed_mermaid_and_drawio(self, tmp_path):
        '''Both mermaid blocks and draw.io references should be rendered.'''
        drawio_file = tmp_path / 'flow.drawio'
        drawio_file.write_text(
            '<mxfile><diagram id="d1" name="Flow"><mxGraphModel/></diagram></mxfile>',
            encoding='utf-8',
        )
        md = (
            '```mermaid\ngraph TD\n  A --> B\n```\n\n'
            f'![Flow]({drawio_file.name})\n'
        )

        def fake_mermaid(source, output_path):
            output_path.write_bytes(b'FAKEPNG')

        def fake_drawio(drawio_path, output_dir, base_name):
            png = output_dir / f'{base_name}_tab1.png'
            png.write_bytes(b'FAKEPNG')
            return [{'source_path': str(png), 'filename': png.name, 'tab_name': 'Flow'}]

        with patch('confluence_utils._render_mermaid', side_effect=fake_mermaid), \
             patch('confluence_utils._render_drawio', side_effect=fake_drawio):
            result = render_diagrams(md, output_dir=str(tmp_path), base_dir=tmp_path)

        assert result.rendered_count == 2
        assert len(result.attachments) == 2
        # One mermaid, one drawio
        mermaid_att = [a for a in result.attachments if 'mermaid' in a['filename']]
        drawio_att = [a for a in result.attachments if 'drawio' in a['filename']]
        assert len(mermaid_att) == 1
        assert len(drawio_att) == 1


# ---------------------------------------------------------------------------
# load_markdown_document — draw.io diagram rendering integration
# ---------------------------------------------------------------------------

class TestLoadMarkdownDocumentDrawio:
    '''Tests that load_markdown_document() renders draw.io diagrams to attachments.'''

    def test_drawio_image_rendered_to_attachment(self, tmp_path):
        '''A ![alt](file.drawio) in a .md file should be rendered to PNG
        attachments and replaced with <ac:image> tags in body_storage.'''
        drawio_file = tmp_path / 'arch.drawio'
        drawio_file.write_text(
            '<mxfile>'
            '<diagram id="d1" name="Overview"><mxGraphModel/></diagram>'
            '</mxfile>',
            encoding='utf-8',
        )
        md_file = tmp_path / 'page.md'
        md_file.write_text(
            '---\ntitle: Test\n---\n\n'
            '# Architecture\n\n'
            '![Architecture](arch.drawio)\n\n'
            'After the diagram.\n',
            encoding='utf-8',
        )

        def fake_render(drawio_path, output_dir, base_name):
            png = output_dir / f'{base_name}_tab1.png'
            png.write_bytes(b'FAKEPNG')
            return [{'source_path': str(png), 'filename': png.name, 'tab_name': 'Overview'}]

        with patch('confluence_utils._render_drawio', side_effect=fake_render):
            doc = load_markdown_document(str(md_file))

        # The diagram should appear as an <ac:image> attachment reference
        assert 'ac:image' in doc.body_storage
        assert 'ri:attachment ri:filename="diagram_drawio_' in doc.body_storage
        # The original .drawio reference should NOT appear
        assert 'arch.drawio' not in doc.body_storage

        # There should be a PNG attachment in the attachments list
        diagram_attachments = [
            a for a in doc.attachments if a['filename'].startswith('diagram_drawio_')
        ]
        assert len(diagram_attachments) >= 1
        assert diagram_attachments[0]['filename'].endswith('.png')

    def test_drawio_rendering_disabled(self, tmp_path):
        '''When render_diagrams_flag=False, .drawio references are left as-is.'''
        drawio_file = tmp_path / 'arch.drawio'
        drawio_file.write_text(
            '<mxfile><diagram id="d1" name="P1"><mxGraphModel/></diagram></mxfile>',
            encoding='utf-8',
        )
        md_file = tmp_path / 'page.md'
        md_file.write_text(
            '---\ntitle: Test\n---\n\n'
            '![Architecture](arch.drawio)\n',
            encoding='utf-8',
        )

        doc = load_markdown_document(str(md_file), render_diagrams_flag=False)

        # No diagram attachments should be present
        diagram_attachments = [
            a for a in doc.attachments if a['filename'].startswith('diagram_drawio_')
        ]
        assert len(diagram_attachments) == 0

    def test_mixed_mermaid_and_drawio_in_document(self, tmp_path):
        '''A file with both mermaid and draw.io diagrams should produce
        attachments for both types.'''
        drawio_file = tmp_path / 'flow.drawio'
        drawio_file.write_text(
            '<mxfile><diagram id="d1" name="Flow"><mxGraphModel/></diagram></mxfile>',
            encoding='utf-8',
        )
        md_file = tmp_path / 'page.md'
        md_file.write_text(
            '---\ntitle: Mixed\n---\n\n'
            '```mermaid\n'
            'graph TD\n'
            '    A --> B\n'
            '```\n\n'
            '![Flow](flow.drawio)\n',
            encoding='utf-8',
        )

        def fake_mermaid(source, output_path):
            output_path.write_bytes(b'FAKEPNG')

        def fake_drawio(drawio_path, output_dir, base_name):
            png = output_dir / f'{base_name}_tab1.png'
            png.write_bytes(b'FAKEPNG')
            return [{'source_path': str(png), 'filename': png.name, 'tab_name': 'Flow'}]

        with patch('confluence_utils._render_mermaid', side_effect=fake_mermaid), \
             patch('confluence_utils._render_drawio', side_effect=fake_drawio):
            doc = load_markdown_document(str(md_file))

        filenames = {a['filename'] for a in doc.attachments}
        mermaid_files = [f for f in filenames if f.startswith('diagram_mermaid_')]
        drawio_files = [f for f in filenames if f.startswith('diagram_drawio_')]
        assert len(mermaid_files) == 1
        assert len(drawio_files) >= 1

        # Both should appear as <ac:image> in the storage
        assert 'ri:attachment ri:filename="diagram_mermaid_' in doc.body_storage
        assert 'ri:attachment ri:filename="diagram_drawio_' in doc.body_storage

    def test_drawio_cwd_fallback_resolution(self, tmp_path):
        '''When a .drawio path is not found relative to base_dir, the resolver
        should fall back to CWD-relative lookup (common for repo-root paths
        referenced from a subdirectory Markdown file).'''
        # Create a directory structure simulating repo layout:
        #   tmp_path/docs/workforce/page.md  (base_dir = docs/workforce/)
        #   tmp_path/diagrams/workforce/arch.drawio
        docs_dir = tmp_path / 'docs' / 'workforce'
        docs_dir.mkdir(parents=True)
        diag_dir = tmp_path / 'diagrams' / 'workforce'
        diag_dir.mkdir(parents=True)

        drawio_file = diag_dir / 'arch.drawio'
        drawio_file.write_text(
            '<mxfile><diagram id="d1" name="Overview"><mxGraphModel/></diagram></mxfile>',
            encoding='utf-8',
        )

        # The markdown references diagrams/workforce/arch.drawio — this is
        # relative to the repo root (CWD), NOT to docs/workforce/.
        md = '![Architecture](diagrams/workforce/arch.drawio)'

        def fake_render(drawio_path, output_dir, base_name):
            png = output_dir / f'{base_name}_tab1.png'
            png.write_bytes(b'FAKEPNG')
            return [{'source_path': str(png), 'filename': png.name, 'tab_name': 'Overview'}]

        # Patch CWD to tmp_path so the fallback finds the file
        with patch('confluence_utils._render_drawio', side_effect=fake_render), \
             patch('confluence_utils.Path.cwd', return_value=tmp_path):
            result = render_diagrams(md, output_dir=str(tmp_path / 'out'), base_dir=docs_dir)

        assert result.rendered_count == 1
        assert len(result.errors) == 0
        assert '![Overview]' in result.markdown

    def test_drawio_skip_in_rewrite_markdown_assets(self, tmp_path):
        '''When render_diagrams_flag is False, a .drawio image reference should
        NOT cause a FileNotFoundError in _rewrite_markdown_assets — the .drawio
        file is simply passed through as-is.'''
        drawio_file = tmp_path / 'arch.drawio'
        drawio_file.write_text(
            '<mxfile><diagram id="d1" name="P1"><mxGraphModel/></diagram></mxfile>',
            encoding='utf-8',
        )
        md_file = tmp_path / 'page.md'
        md_file.write_text(
            '---\ntitle: Test\n---\n\n'
            '![Architecture](arch.drawio)\n',
            encoding='utf-8',
        )

        # With rendering disabled, the .drawio reference should survive without error
        doc = load_markdown_document(str(md_file), render_diagrams_flag=False)
        # The .drawio should NOT be in attachments (it was skipped)
        drawio_attachments = [a for a in doc.attachments if 'drawio' in a['filename']]
        assert len(drawio_attachments) == 0
