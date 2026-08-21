# =============================================================================
# MIT License
# Copyright (c) 2026 Aparavi Software AG
# =============================================================================

"""Unit tests for tool_vertex_search score_threshold filtering.

These are pure-Python unit tests — no server, no live Vertex AI. The node
module is imported under a stubbed ``rocketlib`` so ``IInstance.py`` resolves
without the engine runtime.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

_NODE_DIR = Path(__file__).resolve().parent.parent.parent / 'src' / 'nodes' / 'tool_vertex_search'


def _tool_function(**meta):
    def wrap(fn):
        fn.__tool_meta__ = meta
        return fn

    return wrap


def _build_ai_stubs() -> dict:
    """Stubs used only when the real ``ai`` package is not already imported.

    Never clobber a real ``ai`` / ``ai.common`` package — replacing them with a
    non-package ``types.ModuleType`` leaks into later node tests (see #1640).
    """
    ai = types.ModuleType('ai')
    ai_common = types.ModuleType('ai.common')
    ai_common_tool = types.ModuleType('ai.common.tool')
    ai_common_tool.tool_function = _tool_function
    ai.common = ai_common
    ai_common.tool = ai_common_tool
    return {
        'ai': ai,
        'ai.common': ai_common,
        'ai.common.tool': ai_common_tool,
    }


_saved_rocketlib = sys.modules.get('rocketlib')
_added = []

_rl = types.ModuleType('rocketlib')


class _IInstanceBase:
    pass


_rl.IInstanceBase = _IInstanceBase
_rl.tool_function = _tool_function
sys.modules['rocketlib'] = _rl

for _name, _stub in _build_ai_stubs().items():
    if _name not in sys.modules:
        sys.modules[_name] = _stub
        _added.append(_name)

_added_pkg = 'tool_vertex_search' not in sys.modules
if _added_pkg:
    _pkg = types.ModuleType('tool_vertex_search')
    _pkg.__path__ = [str(_NODE_DIR)]
    sys.modules['tool_vertex_search'] = _pkg

try:
    from tool_vertex_search.IInstance import IInstance  # noqa: E402
finally:
    if _saved_rocketlib is None:
        sys.modules.pop('rocketlib', None)
    else:
        sys.modules['rocketlib'] = _saved_rocketlib
    for _name in _added:
        sys.modules.pop(_name, None)
    if _added_pkg:
        for _name in list(sys.modules):
            if _name == 'tool_vertex_search' or _name.startswith('tool_vertex_search.'):
                sys.modules.pop(_name, None)


def _make_instance(neighbors):
    endpoint = types.SimpleNamespace()
    endpoint.find_neighbors = lambda **kw: [neighbors]
    inst = IInstance()
    inst.glb = types.SimpleNamespace(index_endpoint=endpoint, deployed_index_id='deployed-1')
    return inst, endpoint


def test_search_score_threshold_keeps_higher_similarity():
    neighbors = [
        types.SimpleNamespace(id='close', distance=0.9),
        types.SimpleNamespace(id='far', distance=0.2),
    ]
    inst, _endpoint = _make_instance(neighbors)

    results = inst.search(query_vector=[0.1, 0.2], top_k=10, score_threshold=0.5)

    assert results == [{'id': 'close', 'distance': 0.9}]


def test_search_zero_threshold_keeps_all_neighbors():
    neighbors = [
        types.SimpleNamespace(id='close', distance=0.9),
        types.SimpleNamespace(id='far', distance=0.2),
    ]
    inst, _endpoint = _make_instance(neighbors)

    results = inst.search(query_vector=[0.1, 0.2], top_k=2, score_threshold=0.0)

    assert results == [
        {'id': 'close', 'distance': 0.9},
        {'id': 'far', 'distance': 0.2},
    ]


def test_search_disconnected_returns_error():
    inst = IInstance()
    inst.glb = types.SimpleNamespace(index_endpoint=None, deployed_index_id='deployed-1')

    results = inst.search(query_vector=[0.1], top_k=1)

    assert results == [{'error': 'Vertex AI Index Endpoint is not connected.'}]
