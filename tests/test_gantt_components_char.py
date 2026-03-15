from datetime import datetime, timezone

from agents.gantt_models import PlanningSnapshot


def test_backlog_interpreter_and_dependency_mapper_normalize_and_attach_edges(
    fake_issue_resource_factory,
):
    from agents.gantt_components import BacklogInterpreter, DependencyMapper

    issue = fake_issue_resource_factory(
        key='STL-201',
        summary='Planner component work',
        issue_type='Story',
        status='Blocked',
        assignee=None,
        fix_versions=['12.1.0'],
        updated='2026-02-01T10:00:00.000+0000',
        issuelinks=[
            {
                'type': {
                    'name': 'Blocks',
                    'outward': 'blocks',
                    'inward': 'is blocked by',
                },
                'outwardIssue': {'key': 'STL-202'},
            }
        ],
    )
    issue.raw['fields']['parent'] = {'key': 'STL-200'}

    interpreter = BacklogInterpreter(
        jira_provider=lambda: None,
        now_provider=lambda: datetime(2026, 3, 15, tzinfo=timezone.utc),
        stale_days=30,
    )
    mapper = DependencyMapper()

    normalized = interpreter.normalize_issue(issue)
    assert normalized['parent_key'] == 'STL-200'
    assert normalized['is_stale'] is True
    assert '_issue_links' in normalized

    enriched = mapper.attach_dependency_edges([normalized])[0]
    edge_keys = {
        (edge['source_key'], edge['target_key'], edge['relationship'])
        for edge in enriched['dependency_edges']
    }

    assert '_issue_links' not in enriched
    assert ('STL-200', 'STL-201', 'parent_of') in edge_keys
    assert ('STL-201', 'STL-202', 'blocks') in edge_keys

    graph = mapper.build_graph([enriched])
    assert graph.edge_count == 2
    assert 'STL-201' in graph.blocked_keys
    assert 'STL-202' in graph.blocked_keys


def test_milestone_planner_risk_projector_and_summarizer_build_outputs():
    from agents.gantt_components import (
        DependencyMapper,
        MilestonePlanner,
        PlanningSummarizer,
        RiskProjector,
    )

    issues = [
        {
            'key': 'STL-301',
            'summary': 'Release item',
            'issue_type': 'Story',
            'status': 'In Progress',
            'assignee': '',
            'assignee_display': '',
            'fix_versions': ['12.1.0'],
            'priority': 'High',
            'is_done': False,
            'is_stale': True,
            'age_days': 40,
            'updated_date': '2026-02-01',
            'dependency_edges': [
                {
                    'source_key': 'STL-301',
                    'target_key': 'STL-302',
                    'relationship': 'blocks',
                    'inferred': False,
                    'evidence': 'jira_issue_link',
                }
            ],
        },
        {
            'key': 'STL-302',
            'summary': 'Blocked item',
            'issue_type': 'Story',
            'status': 'Open',
            'assignee': 'Jane Dev',
            'assignee_display': 'Jane Dev',
            'fix_versions': ['12.1.0'],
            'priority': 'Medium',
            'is_done': False,
            'is_stale': False,
            'age_days': 5,
            'updated_date': '2026-03-10',
            'dependency_edges': [],
        },
        {
            'key': 'STL-303',
            'summary': 'Unscheduled backlog',
            'issue_type': 'Bug',
            'status': 'Open',
            'assignee': '',
            'assignee_display': '',
            'fix_versions': [],
            'priority': 'P1-Critical',
            'is_done': False,
            'is_stale': False,
            'age_days': 3,
            'updated_date': '2026-03-12',
            'dependency_edges': [],
        },
    ]

    mapper = DependencyMapper()
    graph = mapper.build_graph(issues)

    planner = MilestonePlanner()
    milestones = planner.build_milestones(
        issues,
        releases=[{'name': '12.1.0', 'releaseDate': '2026-04-01'}],
        dependency_graph=graph,
    )

    risk_projector = RiskProjector()
    evidence_gaps = risk_projector.build_evidence_gaps(issues)
    risks = risk_projector.build_risks(issues, milestones, graph)

    summarizer = PlanningSummarizer()
    overview = summarizer.build_backlog_overview(issues, milestones, graph, risks)
    snapshot = PlanningSnapshot(
        project_key='STL',
        backlog_overview=overview,
        milestones=milestones,
        dependency_graph=graph,
        risks=risks,
        issues=issues,
        evidence_gaps=evidence_gaps,
    )
    markdown = summarizer.format_snapshot(snapshot)

    milestone_names = [milestone.name for milestone in milestones]
    risk_types = {risk.risk_type for risk in risks}

    assert milestone_names == ['12.1.0', 'Unscheduled Backlog']
    assert 'stale_work' in risk_types
    assert 'blocked_work' in risk_types
    assert 'unassigned_priority_work' in risk_types
    assert 'unscheduled_work' in risk_types
    assert overview['blocked_issues'] == 1
    assert overview['risk_count'] == len(risks)
    assert '## Milestone Proposals' in markdown
    assert evidence_gaps[0].startswith('Build, test, release')


def test_backlog_interpreter_build_backlog_jql():
    from agents.gantt_components import BacklogInterpreter
    from agents.gantt_models import PlanningRequest

    request = PlanningRequest(project_key='STL', include_done=False)
    jql = BacklogInterpreter.build_backlog_jql(request)

    assert 'project = "STL"' in jql
    assert 'statusCategory != Done' in jql
    assert jql.endswith('ORDER BY updated DESC')
