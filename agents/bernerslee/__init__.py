##########################################################################################
#
# Module: agents/bernerslee/__init__.py
#
# Description: Berners-Lee Traceability agent package.
#
# Author: Cornelis Networks
#
##########################################################################################
from typing import Any

__all__ = ['BernersLeeAgent', 'LinnaeusAgent']


def __getattr__(name: str) -> Any:
    if name in ('BernersLeeAgent', 'LinnaeusAgent'):
        from agents.bernerslee.agent import BernersLeeAgent, LinnaeusAgent

        if name == 'BernersLeeAgent':
            return BernersLeeAgent
        return LinnaeusAgent

    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
