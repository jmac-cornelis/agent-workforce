##########################################################################################
#
# Module: agents/pliny/__init__.py
#
# Description: Pliny Knowledge Capture agent package.
#
# Author: Cornelis Networks
#
##########################################################################################
from typing import Any

__all__ = ['PlinyAgent', 'HerodotusAgent']


def __getattr__(name: str) -> Any:
    if name in ('PlinyAgent', 'HerodotusAgent'):
        from agents.pliny.agent import PlinyAgent, HerodotusAgent

        if name == 'PlinyAgent':
            return PlinyAgent
        return HerodotusAgent

    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
