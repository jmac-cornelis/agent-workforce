##########################################################################
# Module:      test_feature_planning_orchestrator_char.py
# Description: Characterization tests for Jira actor context in feature-plan
#              execution.
# Author:      Cornelis Networks — AI Engineering Tools
##########################################################################

import pytest

from tools.base import ToolResult


def test_feature_planning_execution_uses_actor_policy_for_ticket_tree_and_links(
    monkeypatch: pytest.MonkeyPatch,
):
    from agents.feature_planning_orchestrator import FeaturePlanningOrchestrator

    monkeypatch.setattr(
        FeaturePlanningOrchestrator,
        '_load_prompt_file',
        staticmethod(lambda: 'feature planning prompt'),
    )
    monkeypatch.setenv('JIRA_EMAIL', 'pm@cornelisnetworks.com')
    monkeypatch.setenv('JIRA_API_TOKEN', 'pm-token')
    monkeypatch.setenv('JIRA_SERVICE_EMAIL', 'scm@cornelisnetworks.com')
    monkeypatch.setenv('JIRA_SERVICE_API_TOKEN', 'svc-token')

    from tools import jira_tools as jira_tools_module

    create_calls = []
    link_calls = []

    monkeypatch.setattr(
        jira_tools_module,
        'create_ticket',
        lambda **kwargs: (
            create_calls.append(kwargs)
            or ToolResult.success({'key': f"STL-{900 + len(create_calls)}"})
        ),
    )
    monkeypatch.setattr(
        jira_tools_module,
        'link_tickets',
        lambda **kwargs: (
            link_calls.append(kwargs)
            or ToolResult.success({'from': kwargs['from_key'], 'to': kwargs['to_key']})
        ),
    )

    agent = FeaturePlanningOrchestrator()
    agent.state.project_key = 'STL'
    agent.state.feature_request = 'ARM RoCE'
    agent.state.jira_plan = {
        'project_key': 'STL',
        'feature_name': 'ARM RoCE',
        'product_family': ['CN6000'],
        'epics': [
            {
                'summary': 'ARM RoCE Epic',
                'description': 'Epic description',
                'components': ['Driver'],
                'labels': ['arm'],
                'stories': [
                    {
                        'summary': 'Story one',
                        'description': 'Story one desc',
                        'components': ['Driver'],
                        'labels': ['arm'],
                        'assignee': 'Jane Dev',
                    },
                    {
                        'summary': 'Story two',
                        'description': 'Story two desc',
                        'components': ['Driver'],
                        'labels': ['arm'],
                        'assignee': 'Jane Dev',
                    },
                ],
            }
        ],
    }
    agent._initiative_was_supplied = True
    agent._requested_by = 'pm@cornelisnetworks.com'
    agent._approved_by = 'pm@cornelisnetworks.com'
    agent._correlation_id = 'feature-plan-001'

    monkeypatch.setattr(
        agent,
        '_resolve_initiative',
        lambda *args, **kwargs: ('STL-100', None),
    )
    monkeypatch.setattr(
        agent,
        '_check_duplicate',
        lambda *args, **kwargs: [],
    )

    response = agent._phase_execution()

    assert response.success is True
    assert len(create_calls) == 3
    assert create_calls[0]['actor_mode'] == 'service_account'
    assert create_calls[0]['policy_rule'] == 'approved_system_batch_apply'
    assert create_calls[0]['requested_by'] == 'pm@cornelisnetworks.com'
    assert create_calls[0]['approved_by'] == 'pm@cornelisnetworks.com'
    assert create_calls[0]['correlation_id'] == 'feature-plan-001'
    assert link_calls[0]['actor_mode'] == 'service_account'
    assert link_calls[0]['policy_rule'] == 'deterministic_low_risk_write'
    assert link_calls[0]['requested_by'] == 'pm@cornelisnetworks.com'
