from core.evidence import load_evidence_bundle


def test_load_evidence_bundle_reads_json_yaml_and_markdown(tmp_path):
    build_path = tmp_path / 'build.json'
    build_path.write_text(
        '{"evidence_type": "build", "title": "Build 101", "summary": "Green build", "facts": ["status: green"]}',
        encoding='utf-8',
    )

    test_path = tmp_path / 'test.yaml'
    test_path.write_text(
        'evidence_type: test\ntitle: Test Suite\nsummary: 42 tests passed\nfacts:\n  - passed: 42\n',
        encoding='utf-8',
    )

    meeting_path = tmp_path / 'meeting_notes.md'
    meeting_path.write_text(
        '# Weekly Sync\n\n- Decision: ship after validation\n- Action: confirm docs\n',
        encoding='utf-8',
    )

    bundle = load_evidence_bundle([
        str(build_path),
        str(test_path),
        str(meeting_path),
    ])

    summary = bundle.to_summary()

    assert summary['record_count'] == 3
    assert summary['by_type']['build'] == 1
    assert summary['by_type']['test'] == 1
    assert summary['source_refs'][0].endswith('build.json')
    assert bundle.has_type('meeting')
