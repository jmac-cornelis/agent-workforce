##########################################################################################
#
# Module: agents/galileo/__init__.py
#
# Description: Galileo Test Planner Agent package.
#
# Author: Cornelis Networks
#
##########################################################################################
from typing import Any

__all__ = ['GalileoAgent', 'AdaAgent']


def __getattr__(name: str) -> Any:
    if name in ('GalileoAgent', 'AdaAgent'):
        from agents.galileo.agent import GalileoAgent, AdaAgent

        if name == 'GalileoAgent':
            return GalileoAgent
        return AdaAgent

    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
