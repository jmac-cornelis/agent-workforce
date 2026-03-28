from types import SimpleNamespace


def test_jira_comment_notifier_builds_hygiene_comment_with_suggestions():
    from agents.drucker_models import DruckerFinding
    from notifications.jira_comments import JiraCommentNotifier

    comment = JiraCommentNotifier.build_hygiene_comment(
        ticket={'key': 'STL-201', 'summary': 'Missing metadata'},
        findings=[
            DruckerFinding(
                finding_id='F001',
                ticket_key='STL-201',
                category='missing_component',
                severity='medium',
                title='Ticket is missing component metadata',
                description='STL-201 has no Jira component set.',
                recommendation='Add a component.',
            )
        ],
        suggested_updates={'components': ['Fabric'], 'priority': 'P1-Critical'},
    )

    assert '[Drucker]' in comment
    assert 'Suggested metadata updates for review:' in comment
    assert 'components: [\'Fabric\']' not in comment
    assert 'components: Fabric' in comment
    assert 'priority: P1-Critical' in comment


def test_jira_comment_notifier_blocks_duplicate_marker_comments():
    from notifications.jira_comments import JiraCommentNotifier

    posted = []

    class _FakeJira:
        def comments(self, ticket_key):
            assert ticket_key == 'STL-201'
            return [
                SimpleNamespace(body='[Drucker] Metadata review\n\nExisting note')
            ]

        def add_comment(self, ticket_key, body):
            posted.append({'ticket_key': ticket_key, 'body': body})

    notifier = JiraCommentNotifier(_FakeJira())

    assert notifier.has_existing_comment('STL-201') is True
    assert notifier.send('STL-201', 'Another message', level='flag', dry_run=False) is False
    assert posted == []
