##########################################################################################
#
# Module: tests/test_shannon_dry_run_flow_char.py
#
# Description: Characterization tests for the Shannon two-step dry-run flow.
#
# Author: Cornelis Networks
#
##########################################################################################

from unittest.mock import MagicMock, patch

from shannon.cards import build_dry_run_preview_card
from shannon.models import AgentChannelRegistration
from shannon.service import ShannonService


def _make_service(mock_poster=None, registry_agents=None):
    from state.shannon_state_store import ShannonStateStore
    from shannon.registry import ShannonAgentRegistry

    with patch.object(ShannonAgentRegistry, '__init__', lambda self, **kw: None):
        svc = ShannonService.__new__(ShannonService)

    svc.registry = MagicMock()
    svc.state_store = ShannonStateStore(storage_dir='/tmp/test_shannon_dryrun')
    svc.poster = mock_poster or MagicMock()
    svc.bot_name = 'Shannon'
    svc.send_welcome_on_install = False

    if registry_agents:
        svc.registry.get_agent.side_effect = lambda aid: registry_agents.get(aid)
        svc.registry.resolve_channel.return_value = None
        svc.registry.list_agents.return_value = list(registry_agents.values())
    return svc


def _drucker_registration(custom_commands=None):
    return AgentChannelRegistration(
        agent_id='drucker',
        display_name='Drucker',
        role='Engineering Hygiene',
        description='test',
        zone='service_infrastructure',
        api_base_url='http://localhost:8201',
        custom_commands=custom_commands or [
            {
                'command': '/pr-hygiene',
                'api_method': 'POST',
                'api_path': '/v1/github/pr-hygiene',
                'mutation': True,
            },
            {
                'command': '/pr-list',
                'api_method': 'GET',
                'api_path': '/v1/github/prs',
            },
        ],
    )


# ---------------------------------------------------------------------------
# build_dry_run_preview_card
# ---------------------------------------------------------------------------

class TestBuildDryRunPreviewCard:

    def test_card_has_dry_run_title(self):
        card = build_dry_run_preview_card('drucker', '/pr-hygiene', {
            'dry_run': True,
            'repo': 'cornelis-networks/omni-path',
            'stale_days': 5,
        })
        title_block = card['body'][0]
        assert 'Dry Run' in title_block['text']
        assert 'Drucker' in title_block['text']

    def test_card_excludes_dry_run_from_facts(self):
        card = build_dry_run_preview_card('drucker', '/pr-hygiene', {
            'dry_run': True,
            'repo': 'cornelis-networks/omni-path',
            'stale_days': 5,
        })
        fact_set = None
        for block in card['body']:
            if block.get('type') == 'FactSet':
                fact_set = block
                break
        assert fact_set is not None
        fact_titles = [f['title'] for f in fact_set['facts']]
        assert 'dry_run' not in fact_titles
        assert 'repo' in fact_titles
        assert 'stale_days' in fact_titles

    def test_card_shows_execute_hint(self):
        card = build_dry_run_preview_card('drucker', '/pr-hygiene', {
            'dry_run': True,
            'repo': 'test/repo',
        })
        texts = [b.get('text', '') for b in card['body']]
        has_execute_hint = any('execute' in t.lower() for t in texts)
        assert has_execute_hint

    def test_card_renders_list_items(self):
        card = build_dry_run_preview_card('drucker', '/transition', {
            'dry_run': True,
            'tickets': [
                {'ticket_key': 'STL-100', 'summary': 'Fix thing'},
                {'ticket_key': 'STL-200', 'summary': 'Another thing'},
            ],
        })
        texts = ' '.join(b.get('text', '') for b in card['body'])
        assert 'STL-100' in texts
        assert 'STL-200' in texts


# ---------------------------------------------------------------------------
# _agent_response_to_shannon — dry_run detection
# ---------------------------------------------------------------------------

class TestDryRunResponseDetection:

    def test_dry_run_response_returns_preview(self):
        svc = _make_service(registry_agents={'drucker': _drucker_registration()})
        result = {
            'ok': True,
            'data': {
                'dry_run': True,
                'repo': 'cornelis-networks/omni-path',
                'stale_days': 5,
            },
        }
        response = svc._agent_response_to_shannon('drucker', '/pr-hygiene', result)
        assert response.decision == 'dry_run_preview'
        assert 'preview' in response.text.lower() or 'dry' in response.text.lower()
        assert response.card is not None

    def test_non_dry_run_response_returns_normal_card(self):
        svc = _make_service(registry_agents={'drucker': _drucker_registration()})
        result = {
            'ok': True,
            'data': {
                'repo': 'cornelis-networks/omni-path',
                'total_open_prs': 5,
                'total_findings': 2,
                'stale_prs': [],
                'missing_reviews': [],
            },
        }
        response = svc._agent_response_to_shannon('drucker', '/pr-hygiene', result)
        assert response.decision != 'dry_run_preview'


# ---------------------------------------------------------------------------
# _handle_registered_agent_command — execute keyword + dry_run injection
# ---------------------------------------------------------------------------

class TestCommandDispatchDryRun:

    @patch.object(ShannonService, '_call_agent_api')
    def test_mutation_command_injects_dry_run_true_by_default(self, mock_call):
        mock_call.return_value = {'ok': True, 'data': {'dry_run': True, 'repo': 'test'}}
        reg = _drucker_registration()
        svc = _make_service(registry_agents={'drucker': reg})
        svc.registry.get_agent.return_value = reg

        svc._handle_registered_agent_command('drucker', '/pr-hygiene repo test/repo')

        call_args = mock_call.call_args
        json_body = call_args.kwargs.get('json_body') or call_args[1].get('json_body') if len(call_args) > 1 else None
        if json_body is None and call_args.args:
            for arg in call_args.args:
                if isinstance(arg, dict) and 'dry_run' in arg:
                    json_body = arg
                    break
        if json_body is None:
            json_body = call_args[0][3] if len(call_args[0]) > 3 else call_args[0][-1]

        assert json_body.get('dry_run') is True

    @patch.object(ShannonService, '_call_agent_api')
    def test_mutation_command_with_execute_sets_dry_run_false(self, mock_call):
        mock_call.return_value = {'ok': True, 'data': {'repo': 'test'}}
        reg = _drucker_registration()
        svc = _make_service(registry_agents={'drucker': reg})
        svc.registry.get_agent.return_value = reg

        svc._handle_registered_agent_command('drucker', '/pr-hygiene repo test/repo execute')

        call_args = mock_call.call_args
        json_body = call_args.kwargs.get('json_body') or call_args[1].get('json_body') if len(call_args) > 1 else None
        if json_body is None and call_args.args:
            for arg in call_args.args:
                if isinstance(arg, dict) and 'dry_run' in arg:
                    json_body = arg
                    break
        if json_body is None:
            json_body = call_args[0][3] if len(call_args[0]) > 3 else call_args[0][-1]

        assert json_body.get('dry_run') is False

    @patch.object(ShannonService, '_call_agent_api')
    def test_non_mutation_command_does_not_inject_dry_run(self, mock_call):
        mock_call.return_value = {'ok': True, 'data': {'prs': []}}
        reg = _drucker_registration()
        svc = _make_service(registry_agents={'drucker': reg})
        svc.registry.get_agent.return_value = reg

        svc._handle_registered_agent_command('drucker', '/pr-list')

        call_args = mock_call.call_args
        json_body = call_args.kwargs.get('json_body')
        assert json_body is None

    @patch.object(ShannonService, '_call_agent_api')
    def test_execute_keyword_stripped_from_args(self, mock_call):
        mock_call.return_value = {'ok': True, 'data': {'repo': 'a/b'}}
        reg = _drucker_registration()
        svc = _make_service(registry_agents={'drucker': reg})
        svc.registry.get_agent.return_value = reg

        svc._handle_registered_agent_command('drucker', '/pr-hygiene repo a/b execute')

        call_args = mock_call.call_args
        json_body = call_args.kwargs.get('json_body') or call_args[1].get('json_body') if len(call_args) > 1 else None
        if json_body is None and call_args.args:
            for arg in call_args.args:
                if isinstance(arg, dict):
                    json_body = arg
                    break
        if json_body is None:
            json_body = call_args[0][3] if len(call_args[0]) > 3 else call_args[0][-1]

        assert 'execute' not in json_body
        assert json_body.get('repo') == 'a/b'
