##########################################################################################
#
# Module: agents/humphrey/__init__.py
#
# Description: Humphrey Release Manager Agent package.
#
# Author: Cornelis Networks
#
##########################################################################################
from typing import Any

__all__ = ['HumphreyAgent', 'HedyAgent']


def __getattr__(name: str) -> Any:
    if name in ('HumphreyAgent', 'HedyAgent'):
        from agents.humphrey.agent import HumphreyAgent, HedyAgent

        if name == 'HumphreyAgent':
            return HumphreyAgent
        return HedyAgent

    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
