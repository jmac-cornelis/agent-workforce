##########################################################################################
#
# Module: tests/test_agent_rename_char.py
#
# Description: Characterization tests for the local agent rename wave.
#              Verifies canonical renamed packages, legacy aliases, and
#              non-deployed local config surfaces.
#
# Author: Cornelis Networks
#
##########################################################################################

import sys
from pathlib import Path


def test_hemingway_exports_legacy_aliases():
    from agents.hemingway import (
        HemingwayDocumentationAgent,
        HemingwayRecordStore,
        HypatiaDocumentationAgent,
        HypatiaRecordStore,
    )
    from agents.hemingway.tools import (
        HemingwayTools,
        HypatiaTools,
        generate_hemingway_documentation,
        generate_hypatia_documentation,
        get_hemingway_record,
        get_hypatia_record,
        list_hemingway_records,
        list_hypatia_records,
    )

    assert HypatiaDocumentationAgent is HemingwayDocumentationAgent
    assert HypatiaRecordStore is HemingwayRecordStore
    assert HypatiaTools is HemingwayTools
    assert generate_hypatia_documentation is generate_hemingway_documentation
    assert get_hypatia_record is get_hemingway_record
    assert list_hypatia_records is list_hemingway_records


def test_agent_cli_accepts_hemingway_command(monkeypatch):
    import agent_cli

    monkeypatch.setattr(
        sys,
        'argv',
        ['agent-cli', 'hemingway', 'generate', '--doc-title', 'Build Notes'],
    )

    args = agent_cli.handle_args()

    assert args.command == 'hemingway'
    assert args.agent_command == 'generate'


def test_agent_cli_accepts_hypatia_legacy_alias(monkeypatch):
    import agent_cli

    monkeypatch.setattr(
        sys,
        'argv',
        ['agent-cli', 'hypatia', 'generate', '--doc-title', 'Build Notes'],
    )

    args = agent_cli.handle_args()

    assert args.command == 'hypatia'
    assert args.agent_command == 'generate'


def test_rename_registry_maps_remaining_agents():
    from agents.rename_registry import agent_display_name, canonical_agent_name

    assert canonical_agent_name('hedy') == 'humphrey'
    assert canonical_agent_name('babbage') == 'mercator'
    assert canonical_agent_name('linnaeus') == 'bernerslee'
    assert canonical_agent_name('herodotus') == 'pliny'
    assert canonical_agent_name('brooks') == 'shackleton'
    assert canonical_agent_name('ada') == 'galileo'
    assert canonical_agent_name('brandeis') == 'blackstone'
    assert agent_display_name('linnaeus') == 'Berners-Lee'


def test_local_renamed_agent_packages_export_legacy_aliases():
    from agents.bernerslee import BernersLeeAgent, LinnaeusAgent
    from agents.galileo import AdaAgent, GalileoAgent
    from agents.humphrey import HedyAgent, HumphreyAgent
    from agents.mercator import BabbageAgent, MercatorAgent
    from agents.pliny import HerodotusAgent, PlinyAgent
    from agents.shackleton import BrooksAgent, ShackletonAgent

    assert HedyAgent is HumphreyAgent
    assert BabbageAgent is MercatorAgent
    assert LinnaeusAgent is BernersLeeAgent
    assert HerodotusAgent is PlinyAgent
    assert BrooksAgent is ShackletonAgent
    assert AdaAgent is GalileoAgent


def test_local_renamed_agent_api_tags_use_new_names():
    from agents.bernerslee.api import router as bernerslee_router
    from agents.galileo.api import router as galileo_router
    from agents.humphrey.api import router as humphrey_router
    from agents.mercator.api import router as mercator_router
    from agents.pliny.api import router as pliny_router
    from agents.shackleton.api import router as shackleton_router

    assert humphrey_router.tags == ['humphrey']
    assert mercator_router.tags == ['mercator']
    assert bernerslee_router.tags == ['bernerslee']
    assert pliny_router.tags == ['pliny']
    assert shackleton_router.tags == ['shackleton']
    assert galileo_router.tags == ['galileo']


def test_blackstone_placeholder_has_local_config():
    config_path = Path('agents/blackstone/config.yaml')
    config_text = config_path.read_text(encoding='utf-8')

    assert 'agent_id: blackstone' in config_text
    assert 'display_name: Blackstone' in config_text
    assert '  - humphrey' in config_text
    assert '  - mercator' in config_text
    assert '  - bernerslee' in config_text
