##########################################################################################
#
# Module: agents/workforce/shannon/cli.py
#
# Description: CLI for testing Shannon — render cards, post to Teams, discover channels.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Any, Dict

from agents.workforce.shannon import cards
from agents.workforce.shannon.graph_client import TeamsGraphClient
from agents.workforce.shannon.registry import ChannelRegistry


def _print_json(data: Dict[str, Any]) -> None:
    print(json.dumps(data, indent=2, default=str))


# ------------------------------------------------------------------
# Card rendering (offline — no Teams credentials needed)
# ------------------------------------------------------------------

def cmd_render_activity(args: argparse.Namespace) -> None:
    details = json.loads(args.details) if args.details else None
    card = cards.activity_card(args.agent_id, args.action, details)
    _print_json(card)


def cmd_render_decision(args: argparse.Namespace) -> None:
    card = cards.decision_card(
        agent_id=args.agent_id,
        decision_type=args.decision_type,
        selected=args.selected,
        rationale=args.rationale,
        decision_id=args.decision_id,
    )
    _print_json(card)


def cmd_render_alert(args: argparse.Namespace) -> None:
    details = json.loads(args.details) if args.details else None
    actions = args.actions.split(',') if args.actions else None
    card = cards.alert_card(args.agent_id, args.severity, args.message,
                            details, actions)
    _print_json(card)


def cmd_render_stats(args: argparse.Namespace) -> None:
    stats = json.loads(args.stats)
    card = cards.stats_card(args.agent_id, stats)
    _print_json(card)


def cmd_render_approval(args: argparse.Namespace) -> None:
    context = json.loads(args.context) if args.context else None
    card = cards.approval_card(args.agent_id, args.approval_type,
                               context, args.approval_id)
    _print_json(card)


# ------------------------------------------------------------------
# Teams discovery (requires credentials)
# ------------------------------------------------------------------

async def _discover_teams() -> None:
    async with TeamsGraphClient() as client:
        teams = await client.list_teams()
        if not teams:
            print('No Teams-enabled groups found (check app permissions).')
            return
        for team in teams:
            print(f"\nTeam: {team['displayName']}  (id: {team['id']})")
            channels = await client.list_channels(team['id'])
            for ch in channels:
                print(f"  Channel: {ch['displayName']}  (id: {ch['id']})")


def cmd_discover(args: argparse.Namespace) -> None:
    asyncio.run(_discover_teams())


# ------------------------------------------------------------------
# Post message (requires credentials + registry)
# ------------------------------------------------------------------

async def _post_message(channel_name: str, text: str) -> None:
    registry = ChannelRegistry()
    mapping = registry.resolve_or_raise(channel_name)
    async with TeamsGraphClient() as client:
        result = await client.send_message(
            team_id=mapping.team_id,
            channel_id=mapping.channel_id,
            content=text,
        )
        print(f"Message sent. ID: {result.get('id', 'unknown')}")


def cmd_post(args: argparse.Namespace) -> None:
    asyncio.run(_post_message(args.channel, args.text))


async def _post_card_file(channel_name: str, card_path: str) -> None:
    registry = ChannelRegistry()
    mapping = registry.resolve_or_raise(channel_name)
    with open(card_path, 'r', encoding='utf-8') as f:
        card = json.load(f)
    async with TeamsGraphClient() as client:
        result = await client.send_adaptive_card(
            team_id=mapping.team_id,
            channel_id=mapping.channel_id,
            card=card,
        )
        print(f"Card sent. ID: {result.get('id', 'unknown')}")


def cmd_post_card(args: argparse.Namespace) -> None:
    asyncio.run(_post_card_file(args.channel, args.file))


# ------------------------------------------------------------------
# List configured channels
# ------------------------------------------------------------------

def cmd_channels(args: argparse.Namespace) -> None:
    config_path = args.config if hasattr(args, 'config') and args.config else None
    registry = ChannelRegistry(config_path)
    for m in registry.list_channels():
        status = '✓' if m.enabled else '✗'
        print(f'  {status} {m.name:20s} {m.channel_display_name:30s} '
              f'team={m.team_id or "(unset)":20s} ch={m.channel_id or "(unset)"}')


# ------------------------------------------------------------------
# Argument parser
# ------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='shannon',
        description='Shannon Communications agent CLI',
    )
    sub = parser.add_subparsers(dest='command', required=True)

    # --- render sub-commands ---
    render = sub.add_parser('render', help='Render Adaptive Card JSON to stdout')
    render_sub = render.add_subparsers(dest='card_type', required=True)

    p = render_sub.add_parser('activity')
    p.add_argument('--agent-id', required=True)
    p.add_argument('--action', required=True)
    p.add_argument('--details', default=None, help='JSON string')
    p.set_defaults(func=cmd_render_activity)

    p = render_sub.add_parser('decision')
    p.add_argument('--agent-id', required=True)
    p.add_argument('--decision-type', required=True)
    p.add_argument('--selected', required=True)
    p.add_argument('--rationale', required=True)
    p.add_argument('--decision-id', default=None)
    p.set_defaults(func=cmd_render_decision)

    p = render_sub.add_parser('alert')
    p.add_argument('--agent-id', required=True)
    p.add_argument('--severity', required=True, choices=['critical', 'high', 'medium', 'low'])
    p.add_argument('--message', required=True)
    p.add_argument('--details', default=None, help='JSON string')
    p.add_argument('--actions', default=None, help='Comma-separated suggested actions')
    p.set_defaults(func=cmd_render_alert)

    p = render_sub.add_parser('stats')
    p.add_argument('--agent-id', required=True)
    p.add_argument('--stats', required=True, help='JSON string of stats')
    p.set_defaults(func=cmd_render_stats)

    p = render_sub.add_parser('approval')
    p.add_argument('--agent-id', required=True)
    p.add_argument('--approval-type', required=True)
    p.add_argument('--context', default=None, help='JSON string')
    p.add_argument('--approval-id', default=None)
    p.set_defaults(func=cmd_render_approval)

    # --- discover ---
    p = sub.add_parser('discover', help='Discover Teams and channels via Graph API')
    p.set_defaults(func=cmd_discover)

    # --- post ---
    p = sub.add_parser('post', help='Post a text message to a channel')
    p.add_argument('--channel', required=True, help='Logical channel name')
    p.add_argument('--text', required=True, help='Message text')
    p.set_defaults(func=cmd_post)

    # --- post-card ---
    p = sub.add_parser('post-card', help='Post an Adaptive Card from a JSON file')
    p.add_argument('--channel', required=True, help='Logical channel name')
    p.add_argument('--file', required=True, help='Path to card JSON file')
    p.set_defaults(func=cmd_post_card)

    # --- channels ---
    p = sub.add_parser('channels', help='List configured channels')
    p.add_argument('--config', default=None, help='Path to config.yaml')
    p.set_defaults(func=cmd_channels)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
