##########################################################################################
#
# Module: agents/hemingway/__init__.py
#
# Description: Hemingway documentation agent package.
#              Lazy imports to avoid circular dependency with agents.base → tools.
#
# Author: Cornelis Networks
#
##########################################################################################

_LAZY_MAP = {
    'HemingwayDocumentationAgent': ('agents.hemingway.agent', 'HemingwayDocumentationAgent'),
    'HypatiaDocumentationAgent': ('agents.hemingway.agent', 'HemingwayDocumentationAgent'),
    'HemingwayRecordStore': ('agents.hemingway.state.record_store', 'HemingwayRecordStore'),
    'HypatiaRecordStore': ('agents.hemingway.state.record_store', 'HemingwayRecordStore'),
}


def __getattr__(name):
    if name in _LAZY_MAP:
        import importlib
        module_path, attr = _LAZY_MAP[name]
        mod = importlib.import_module(module_path)
        return getattr(mod, attr)
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')


__all__ = list(_LAZY_MAP.keys())
