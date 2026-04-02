##########################################################################################
#
# Module: agents/shackleton/__init__.py
#
# Description: Shackleton Delivery Manager agent package.
#
# Author: Cornelis Networks
#
##########################################################################################
from typing import Any

__all__ = ['ShackletonAgent', 'BrooksAgent']


def __getattr__(name: str) -> Any:
    if name in ('ShackletonAgent', 'BrooksAgent'):
        from agents.shackleton.agent import ShackletonAgent, BrooksAgent

        if name == 'ShackletonAgent':
            return ShackletonAgent
        return BrooksAgent

    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
