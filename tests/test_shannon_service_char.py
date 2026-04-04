import base64
import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from shannon.app import create_app
from shannon.outgoing_webhook import extract_hmac_signature
from shannon.poster import MemoryPoster
from shannon.registry import ShannonAgentRegistry
from shannon.service import ShannonService
from agents.shannon.state_store import ShannonStateStore


def _message_activity(text: str = '<at>Shannon</at> /stats') -> dict:
    return {
        'type': 'message',
        'id': 'activity-1001',
        'text': text,
        'serviceUrl': 'https://smba.trafficmanager.net/amer/',
        'conversation': {
            'id': '19:conversation@thread.tacv2',
            'conversationType': 'channel',
            'tenantId': 'tenant-001',
        },
        'channelData': {
            'team': {'id': 'team-001'},
            'channel': {'id': '19:channel@thread.tacv2', 'name': 'agent-shannon'},
            'tenant': {'id': 'tenant-001'},
        },
        'from': {'id': 'user-001', 'name': 'Test User'},
        'recipient': {'id': 'bot-001', 'name': 'Shannon'},
    }


def _conversation_update_activity() -> dict:
    payload = _message_activity(text='')
    payload['type'] = 'conversationUpdate'
    payload['id'] = 'activity-setup'
    return payload


def _agent_message_activity(channel_name: str, text: str) -> dict:
    payload = _message_activity(text=text)
    payload['channelData']['channel']['name'] = channel_name
    payload['channelData']['channel']['id'] = f'19:{channel_name}@thread.tacv2'
    return payload


def _service(tmp_path) -> tuple[ShannonService, MemoryPoster]:
    poster = MemoryPoster()
    registry = ShannonAgentRegistry()
    store = ShannonStateStore(storage_dir=str(tmp_path / 'shannon'))
    service = ShannonService(
        registry=registry,
        state_store=store,
        poster=poster,
        bot_name='Shannon',
        send_welcome_on_install=True,
    )
    return service, poster


def test_process_message_activity_posts_stats_reply(tmp_path):
    service, poster = _service(tmp_path)

    result = service.process_teams_activity(_message_activity())

    assert result['ok'] is True
    assert result['command'] == '/stats'
    assert result['decision'] == 'reported_service_stats'
    assert poster.sent[-1]['kind'] == 'reply'
    assert 'Shannon is online.' in poster.sent[-1]['activity']['text']

    stored = service.state_store.get_conversation_reference(
        channel_id='19:channel@thread.tacv2'
    )
    assert stored is not None
    assert stored.user_name == 'Test User'


def test_conversation_update_stores_reference_and_welcome(tmp_path):
    service, poster = _service(tmp_path)

    result = service.process_teams_activity(_conversation_update_activity())

    assert result['ok'] is True
    assert result['activity_type'] == 'conversationUpdate'
    assert result['post_result']['mode'] == 'memory'
    assert poster.sent[-1]['kind'] == 'conversation'
    assert 'Shannon is online in this channel.' in poster.sent[-1]['activity']['text']


def test_post_notification_uses_stored_conversation_reference(tmp_path):
    service, poster = _service(tmp_path)
    service.process_teams_activity(_conversation_update_activity())

    result = service.post_notification(
        agent_id='shannon',
        title='Shannon Notification Test',
        text='This is a direct Shannon notification.',
    )

    assert result['ok'] is True
    assert result['agent_id'] == 'shannon'
    assert poster.sent[-1]['kind'] == 'conversation'
    assert poster.sent[-1]['activity']['text'] == 'This is a direct Shannon notification.'


def test_process_gantt_message_posts_snapshot_reply(tmp_path, monkeypatch):
    service, poster = _service(tmp_path)
    gantt_registration = service.registry.get_agent('gantt')
    assert gantt_registration is not None

    def _fake_call(registration, method, path, params=None, json_body=None):
        assert registration.agent_id == 'gantt'
        assert method == 'POST'
        assert path == '/v1/planning/snapshot'
        assert params is None
        assert json_body == {'project_key': 'STL'}
        return {
            'ok': True,
            'data': {
                'snapshot': {
                    'project_key': 'STL',
                    'created_at': '2026-03-25T12:00:00+00:00',
                    'backlog_overview': {
                        'total_issues': 4,
                        'blocked_issues': 1,
                        'stale_issues': 0,
                    },
                    'milestones': [
                        {
                            'name': '12.1.1.x',
                            'open_issues': 2,
                            'blocked_issues': 1,
                        }
                    ],
                    'dependency_graph': {'edge_count': 2},
                    'risks': [],
                }
            },
        }

    monkeypatch.setattr(service, '_call_agent_api', _fake_call)

    activity = _agent_message_activity(
        'agent-gantt',
        '<at>Shannon</at> /planning-snapshot STL',
    )
    activity['channelData']['team']['id'] = gantt_registration.team_id

    result = service.process_teams_activity(activity)

    assert result['ok'] is True
    assert result['agent_id'] == 'gantt'
    assert result['command'] == '/planning-snapshot'
    assert poster.sent[-1]['kind'] == 'reply'
    assert 'STL: 4 issues' in poster.sent[-1]['activity']['text']
    card = poster.sent[-1]['activity']['attachments'][0]['content']
    assert card['body'][0]['text'] == 'Gantt Planning Snapshot — STL'


def test_process_gantt_release_survey_posts_reply(tmp_path, monkeypatch):
    service, poster = _service(tmp_path)
    gantt_registration = service.registry.get_agent('gantt')
    assert gantt_registration is not None

    def _fake_call(registration, method, path, params=None, json_body=None):
        assert registration.agent_id == 'gantt'
        assert method == 'POST'
        assert path == '/v1/release-survey/run'
        assert params is None
        assert json_body == {'project_key': 'STL'}
        return {
            'ok': True,
            'data': {
                'survey': {
                    'project_key': 'STL',
                    'created_at': '2026-03-25T12:00:00+00:00',
                    'releases_surveyed': ['12.2.0.x'],
                    'total_tickets': 10,
                    'done_count': 4,
                    'in_progress_count': 3,
                    'remaining_count': 2,
                    'blocked_count': 1,
                    'release_summaries': [
                        {
                            'release': '12.2.0.x',
                            'done_count': 4,
                            'in_progress_count': 3,
                            'remaining_count': 2,
                            'blocked_count': 1,
                        }
                    ],
                }
            },
        }

    monkeypatch.setattr(service, '_call_agent_api', _fake_call)

    activity = _agent_message_activity(
        'agent-gantt',
        '<at>Shannon</at> /release-survey STL',
    )
    activity['channelData']['team']['id'] = gantt_registration.team_id

    result = service.process_teams_activity(activity)

    assert result['ok'] is True
    assert result['agent_id'] == 'gantt'
    assert result['command'] == '/release-survey'
    assert poster.sent[-1]['kind'] == 'reply'
    assert 'STL: 4 done, 3 in progress, 2 remaining, 1 blocked' in (
        poster.sent[-1]['activity']['text']
    )
    card = poster.sent[-1]['activity']['attachments'][0]['content']
    assert card['body'][0]['text'] == 'Gantt Release Survey — STL'


def test_process_drucker_issue_check_posts_reply(tmp_path, monkeypatch):
    service, poster = _service(tmp_path)
    drucker_registration = service.registry.get_agent('drucker')
    assert drucker_registration is not None
    # Clear webhook URL so test MemoryPoster is used instead of a real WorkflowsPoster
    drucker_registration.notifications_webhook_url = ''

    def _fake_call(registration, method, path, params=None, json_body=None):
        assert registration.agent_id == 'drucker'
        assert method == 'POST'
        assert path == '/v1/hygiene/issue'
        assert params is None
        assert json_body == {'project_key': 'STL', 'ticket_key': 'STL-201'}
        return {
            'ok': True,
            'data': {
                'report': {
                    'project_key': 'STL',
                    'report_id': 'rep-issue-1',
                    'created_at': '2026-03-25T12:00:00+00:00',
                    'summary': {
                        'finding_count': 2,
                        'action_count': 2,
                    },
                    'findings': [
                        {
                            'ticket_key': 'STL-201',
                            'severity': 'high',
                            'description': 'Missing required fields.',
                        }
                    ],
                    'proposed_actions': [
                        {'action_type': 'update'},
                        {'action_type': 'comment'},
                    ],
                }
            },
        }

    monkeypatch.setattr(service, '_call_agent_api', _fake_call)

    activity = _agent_message_activity(
        'agent-drucker',
        '<at>Shannon</at> /issue-check project_key STL ticket_key STL-201',
    )
    activity['channelData']['team']['id'] = drucker_registration.team_id

    result = service.process_teams_activity(activity)

    assert result['ok'] is True
    assert result['agent_id'] == 'drucker'
    assert result['command'] == '/issue-check'
    assert poster.sent[-1]['kind'] == 'reply'
    assert 'STL: 2 findings, 2 proposed actions' in poster.sent[-1]['activity']['text']


def test_process_drucker_intake_report_posts_reply(tmp_path, monkeypatch):
    service, poster = _service(tmp_path)
    drucker_registration = service.registry.get_agent('drucker')
    assert drucker_registration is not None
    drucker_registration.notifications_webhook_url = ''

    def _fake_call(registration, method, path, params=None, json_body=None):
        assert registration.agent_id == 'drucker'
        assert method == 'POST'
        assert path == '/v1/hygiene/intake'
        assert params is None
        assert json_body == {'project_key': 'STL'}
        return {
            'ok': True,
            'data': {
                'report': {
                    'project_key': 'STL',
                    'report_id': 'rep-intake-1',
                    'created_at': '2026-03-25T12:00:00+00:00',
                    'summary': {
                        'finding_count': 2,
                        'action_count': 1,
                        'monitor_scope': 'recent_ticket_intake',
                    },
                    'findings': [
                        {
                            'ticket_key': 'STL-301',
                            'severity': 'medium',
                            'description': 'Missing recommended fields.',
                        }
                    ],
                    'proposed_actions': [
                        {'action_type': 'comment'},
                    ],
                }
            },
        }

    monkeypatch.setattr(service, '_call_agent_api', _fake_call)

    activity = _agent_message_activity(
        'agent-drucker',
        '<at>Shannon</at> /intake-report STL',
    )
    activity['channelData']['team']['id'] = drucker_registration.team_id

    result = service.process_teams_activity(activity)

    assert result['ok'] is True
    assert result['agent_id'] == 'drucker'
    assert result['command'] == '/intake-report'
    assert poster.sent[-1]['kind'] == 'reply'
    assert 'STL: 2 findings, 1 proposed actions' in poster.sent[-1]['activity']['text']
    card = poster.sent[-1]['activity']['attachments'][0]['content']
    assert card['body'][0]['text'] == 'Drucker Ticket Intake — STL'


def test_process_drucker_bug_activity_posts_reply(tmp_path, monkeypatch):
    service, poster = _service(tmp_path)
    drucker_registration = service.registry.get_agent('drucker')
    assert drucker_registration is not None
    drucker_registration.notifications_webhook_url = ''

    def _fake_call(registration, method, path, params=None, json_body=None):
        assert registration.agent_id == 'drucker'
        assert method == 'POST'
        assert path == '/v1/activity/bugs'
        assert params is None
        assert json_body == {'project_key': 'STL', 'target_date': '2026-03-25'}
        return {
            'ok': True,
            'data': {
                'project': 'STL',
                'date': '2026-03-25',
                'summary': {
                    'bugs_opened': 1,
                    'status_transitions': 2,
                    'bugs_with_comments': 1,
                    'total_active_bugs': 3,
                },
                'opened': [{'key': 'STL-201', 'summary': 'Fabric issue', 'priority': 'High'}],
                'status_changed': [],
                'commented': [],
            },
        }

    monkeypatch.setattr(service, '_call_agent_api', _fake_call)

    activity = _agent_message_activity(
        'agent-drucker',
        '<at>Shannon</at> /bug-activity project_key STL target_date 2026-03-25',
    )
    activity['channelData']['team']['id'] = drucker_registration.team_id

    result = service.process_teams_activity(activity)

    assert result['ok'] is True
    assert result['agent_id'] == 'drucker'
    assert result['command'] == '/bug-activity'
    assert poster.sent[-1]['kind'] == 'reply'
    assert 'STL: 1 opened, 2 status changes, 1 commented' in poster.sent[-1]['activity']['text']
    card = poster.sent[-1]['activity']['attachments'][0]['content']
    assert card['body'][0]['text'] == 'Bug Activity — STL'


def test_app_endpoints_expose_health_and_messages(tmp_path):
    service, _poster = _service(tmp_path)
    client = TestClient(create_app(service))

    health = client.get('/v1/bot/health')
    assert health.status_code == 200
    assert health.json()['service'] == 'shannon'

    message = client.post('/api/messages', json=_message_activity('<at>Shannon</at> /busy'))
    assert message.status_code == 200
    assert message.json()['command'] == '/busy'

    decisions = client.get('/v1/status/decisions')
    assert decisions.status_code == 200
    assert len(decisions.json()) >= 1


def test_notify_endpoint_requires_stored_reference(tmp_path):
    service, _poster = _service(tmp_path)
    client = TestClient(create_app(service))

    response = client.post(
        '/v1/bot/notify',
        json={
            'agent_id': 'shannon',
            'title': 'Test',
            'text': 'Need a channel reference first.',
        },
    )

    assert response.status_code == 400
    assert 'No stored conversation reference' in response.json()['detail']


def test_outgoing_webhook_signature_helpers():
    body = b'{"type":"message"}'
    secret = base64.b64encode(b'shannon-secret').decode('utf-8')
    digest = hmac.new(
        base64.b64decode(secret),
        body,
        hashlib.sha256,
    ).digest()
    provided = base64.b64encode(digest).decode('utf-8')

    assert extract_hmac_signature(f'HMAC {provided}') == provided


def test_outgoing_webhook_endpoint_validates_hmac_and_returns_sync_reply(tmp_path, monkeypatch):
    secret = base64.b64encode(b'shannon-secret').decode('utf-8')
    monkeypatch.setenv('SHANNON_TEAMS_OUTGOING_WEBHOOK_SECRET', secret)

    service, _poster = _service(tmp_path)
    client = TestClient(create_app(service))

    payload = _message_activity('<at>Shannon</at> /stats')
    body = json.dumps(payload).encode('utf-8')
    digest = hmac.new(
        base64.b64decode(secret),
        body,
        hashlib.sha256,
    ).digest()
    signature = base64.b64encode(digest).decode('utf-8')

    response = client.post(
        '/v1/teams/outgoing-webhook',
        content=body,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'HMAC {signature}',
        },
    )

    assert response.status_code == 200
    assert response.json()['type'] == 'message'
    assert 'Shannon is online.' in response.json()['text']


def test_outgoing_webhook_endpoint_rejects_bad_signature(tmp_path, monkeypatch):
    monkeypatch.setenv(
        'SHANNON_TEAMS_OUTGOING_WEBHOOK_SECRET',
        base64.b64encode(b'shannon-secret').decode('utf-8'),
    )

    service, _poster = _service(tmp_path)
    client = TestClient(create_app(service))

    response = client.post(
        '/v1/teams/outgoing-webhook',
        json=_message_activity('<at>Shannon</at> /stats'),
        headers={'Authorization': 'HMAC invalid'},
    )

    assert response.status_code == 401
