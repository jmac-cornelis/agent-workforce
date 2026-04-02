##########################################################################################
#
# Module: agents/mercator/__init__.py
#
# Description: Mercator Version Manager agent package.
#
# Author: Cornelis Networks
#
##########################################################################################
from typing import Any

__all__ = ['MercatorAgent', 'BabbageAgent']


def __getattr__(name: str) -> Any:
    if name in ('MercatorAgent', 'BabbageAgent'):
        from agents.mercator.agent import MercatorAgent, BabbageAgent

        if name == 'MercatorAgent':
            return MercatorAgent
        return BabbageAgent

    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
