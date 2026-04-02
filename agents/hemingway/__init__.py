##########################################################################################
#
# Module: agents/hemingway/__init__.py
#
# Description: Hemingway Documentation agent package.
#
# Author: Cornelis Networks
#
##########################################################################################

from typing import Any

__all__ = [
    'HemingwayDocumentationAgent',
    'HypatiaDocumentationAgent',
    'HemingwayRecordStore',
    'HypatiaRecordStore',
]


def __getattr__(name: str) -> Any:
    if name in ('HemingwayDocumentationAgent', 'HypatiaDocumentationAgent'):
        from agents.hemingway.agent import (
            HemingwayDocumentationAgent,
            HypatiaDocumentationAgent,
        )

        if name == 'HemingwayDocumentationAgent':
            return HemingwayDocumentationAgent
        return HypatiaDocumentationAgent

    if name in ('HemingwayRecordStore', 'HypatiaRecordStore'):
        from agents.hemingway.state.record_store import (
            HemingwayRecordStore,
            HypatiaRecordStore,
        )

        if name == 'HemingwayRecordStore':
            return HemingwayRecordStore
        return HypatiaRecordStore

    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
