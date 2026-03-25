import pytest


def test_drucker_learning_store_predicts_component_fix_version_and_priority():
    from state.drucker_learning_store import DruckerLearningStore

    store = DruckerLearningStore(db_path=':memory:', min_observations=2)

    store.record_ticket({
        'key': 'STL-101',
        'summary': 'Fabric link instability',
        'reporter': 'alice',
        'components': ['Fabric'],
        'fix_versions': ['12.1.0'],
        'priority': 'P1-Critical',
    })
    store.record_ticket({
        'key': 'STL-102',
        'summary': 'Fabric link reset regression',
        'reporter': 'alice',
        'components': ['Fabric'],
        'fix_versions': ['12.1.0'],
        'priority': 'P1-Critical',
    })

    component, component_confidence = store.get_field_prediction(
        'components',
        {
            'summary': 'Fabric link missing metadata',
            'reporter': 'alice',
        },
    )
    fix_version, fix_version_confidence = store.get_field_prediction(
        'fix_versions',
        {
            'summary': 'Fabric link missing metadata',
            'reporter': 'alice',
        },
    )
    priority, priority_confidence = store.get_field_prediction(
        'priority',
        {
            'summary': 'Fabric link missing metadata',
            'reporter': 'alice',
        },
    )

    assert component == 'Fabric'
    assert fix_version == '12.1.0'
    assert priority == 'P1-Critical'
    assert component_confidence > 0.0
    assert fix_version_confidence > 0.0
    assert priority_confidence > 0.0


def test_drucker_learning_store_requires_minimum_observations():
    from state.drucker_learning_store import DruckerLearningStore

    store = DruckerLearningStore(db_path=':memory:', min_observations=3)
    store.record_ticket({
        'key': 'STL-201',
        'summary': 'Fabric issue',
        'reporter': 'alice',
        'components': ['Fabric'],
        'fix_versions': ['12.1.0'],
        'priority': 'P1-Critical',
    })
    store.record_ticket({
        'key': 'STL-202',
        'summary': 'Fabric issue again',
        'reporter': 'alice',
        'components': ['Fabric'],
        'fix_versions': ['12.1.0'],
        'priority': 'P1-Critical',
    })

    component, confidence = store.get_field_prediction(
        'components',
        {'summary': 'Fabric issue missing metadata', 'reporter': 'alice'},
    )

    assert component == ''
    assert confidence == 0.0


def test_drucker_learning_store_dedupes_repeated_ticket_learning():
    from state.drucker_learning_store import DruckerLearningStore

    store = DruckerLearningStore(db_path=':memory:', min_observations=2)
    ticket = {
        'key': 'STL-301',
        'summary': 'Fabric issue dedupe check',
        'reporter': 'alice',
        'components': ['Fabric'],
        'fix_versions': ['12.1.0'],
        'priority': 'P1-Critical',
    }

    store.record_ticket(ticket)
    store.record_ticket(dict(ticket))

    component, confidence = store.get_field_prediction(
        'components',
        {'summary': 'Fabric issue missing metadata', 'reporter': 'alice'},
    )

    assert component == ''
    assert confidence == 0.0
    assert store.get_stats()['tables']['learned_tickets'] == 1
