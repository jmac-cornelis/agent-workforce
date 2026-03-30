##########################################################################################
#
# Module: agents/workforce/shannon/registry.py
#
# Description: Channel registry — maps agent names to Teams team/channel IDs.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

log = logging.getLogger(os.path.basename(sys.argv[0]))

_DEFAULT_CONFIG = Path(__file__).parent / 'config.yaml'


@dataclass
class ChannelMapping:
    """Maps a logical channel name to a Teams team + channel ID pair.

    Necessary: callers need to know the structure to resolve names to IDs.
    """
    name: str
    team_id: str
    channel_id: str
    team_name: str = ''
    channel_display_name: str = ''
    enabled: bool = True


@dataclass
class RegistryConfig:
    """Top-level registry configuration loaded from YAML."""
    default_team_id: str = ''
    default_team_name: str = ''
    channels: Dict[str, ChannelMapping] = field(default_factory=dict)


class ChannelRegistry:
    """Resolves logical channel names (e.g. 'drucker', 'gantt') to
    Microsoft Teams team_id / channel_id pairs.

    Loads mappings from a YAML config file. Supports runtime overrides
    and dynamic discovery via the Graph client.
    """

    def __init__(self, config_path: Optional[str] = None):
        self._config_path = Path(config_path) if config_path else _DEFAULT_CONFIG
        self._config: Optional[RegistryConfig] = None
        self._load()

    def _load(self) -> None:
        if not self._config_path.exists():
            log.warning(f'Registry config not found: {self._config_path}')
            self._config = RegistryConfig()
            return

        with open(self._config_path, 'r', encoding='utf-8') as f:
            raw = yaml.safe_load(f) or {}

        teams_cfg = raw.get('teams', {})
        default_team_id = teams_cfg.get('default_team_id', '')
        default_team_name = teams_cfg.get('default_team_name', '')

        channels: Dict[str, ChannelMapping] = {}
        for name, ch_data in raw.get('channels', {}).items():
            channels[name] = ChannelMapping(
                name=name,
                team_id=ch_data.get('team_id', default_team_id),
                channel_id=ch_data.get('channel_id', ''),
                team_name=ch_data.get('team_name', default_team_name),
                channel_display_name=ch_data.get('display_name', name),
                enabled=ch_data.get('enabled', True),
            )

        self._config = RegistryConfig(
            default_team_id=default_team_id,
            default_team_name=default_team_name,
            channels=channels,
        )
        log.info(
            f'Loaded {len(channels)} channel mappings from {self._config_path}'
        )

    def resolve(self, channel_name: str) -> Optional[ChannelMapping]:
        """Look up a channel by logical name. Returns None if not found or disabled."""
        assert self._config is not None
        mapping = self._config.channels.get(channel_name)
        if mapping and not mapping.enabled:
            log.debug(f'Channel {channel_name!r} is disabled')
            return None
        return mapping

    def resolve_or_raise(self, channel_name: str) -> ChannelMapping:
        """Look up a channel by name; raise KeyError if missing/disabled."""
        mapping = self.resolve(channel_name)
        if mapping is None:
            available = ', '.join(self.list_channel_names())
            raise KeyError(
                f'Channel {channel_name!r} not found or disabled. '
                f'Available: {available}'
            )
        return mapping

    def list_channel_names(self) -> List[str]:
        """Return all enabled channel names."""
        assert self._config is not None
        return [
            name for name, m in self._config.channels.items() if m.enabled
        ]

    def list_channels(self) -> List[ChannelMapping]:
        """Return all enabled channel mappings."""
        assert self._config is not None
        return [m for m in self._config.channels.values() if m.enabled]

    def add_channel(
        self,
        name: str,
        team_id: str,
        channel_id: str,
        team_name: str = '',
        display_name: str = '',
    ) -> None:
        """Register a channel mapping at runtime (not persisted to YAML)."""
        assert self._config is not None
        self._config.channels[name] = ChannelMapping(
            name=name,
            team_id=team_id,
            channel_id=channel_id,
            team_name=team_name,
            channel_display_name=display_name or name,
        )
        log.info(f'Added runtime channel mapping: {name}')

    def remove_channel(self, name: str) -> bool:
        """Remove a channel mapping. Returns True if it existed."""
        assert self._config is not None
        if name in self._config.channels:
            del self._config.channels[name]
            log.info(f'Removed channel mapping: {name}')
            return True
        return False

    @property
    def default_team_id(self) -> str:
        assert self._config is not None
        return self._config.default_team_id

    def to_dict(self) -> Dict[str, Any]:
        """Serialize registry state for diagnostics."""
        assert self._config is not None
        return {
            'default_team_id': self._config.default_team_id,
            'default_team_name': self._config.default_team_name,
            'channels': {
                name: {
                    'team_id': m.team_id,
                    'channel_id': m.channel_id,
                    'display_name': m.channel_display_name,
                    'enabled': m.enabled,
                }
                for name, m in self._config.channels.items()
            },
        }
