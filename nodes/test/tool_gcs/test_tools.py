# =============================================================================
# MIT License
# Copyright (c) 2026 Aparavi Software AG
# =============================================================================

"""Unit tests for tool_gcs download size-cap, prefix joining, and temp-file retention.

These are pure-Python unit tests — no server, no live GCS. The node module is
imported under a stubbed ``rocketlib`` so ``IInstance.py`` / ``IGlobal.py``
resolve without the engine runtime.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

_NODE_DIR = Path(__file__).resolve().parent.parent.parent / 'src' / 'nodes' / 'tool_gcs'


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
    ai_common_config = types.ModuleType('ai.common.config')
    ai_common_tool.tool_function = _tool_function
    ai_common_config.Config = type('Config', (), {})
    ai.common = ai_common
    ai_common.tool = ai_common_tool
    ai_common.config = ai_common_config
    return {
        'ai': ai,
        'ai.common': ai_common,
        'ai.common.tool': ai_common_tool,
        'ai.common.config': ai_common_config,
    }


_saved_rocketlib = sys.modules.get('rocketlib')
_added = []

_rl = types.ModuleType('rocketlib')


class _IInstanceBase:
    pass


class _IGlobalBase:
    pass


_rl.IInstanceBase = _IInstanceBase
_rl.IGlobalBase = _IGlobalBase
_rl.tool_function = _tool_function
_rl.OPEN_MODE = types.SimpleNamespace(CONFIG='config')
_rl.debug = lambda *a, **kw: None
_rl.warning = lambda *a, **kw: None
sys.modules['rocketlib'] = _rl

for _name, _stub in _build_ai_stubs().items():
    if _name not in sys.modules:
        sys.modules[_name] = _stub
        _added.append(_name)

_added_pkg = 'tool_gcs' not in sys.modules
if _added_pkg:
    _pkg = types.ModuleType('tool_gcs')
    _pkg.__path__ = [str(_NODE_DIR)]
    sys.modules['tool_gcs'] = _pkg

try:
    from tool_gcs.IGlobal import IGlobal  # noqa: E402
    from tool_gcs.IInstance import IInstance, join_gcs_prefix  # noqa: E402
finally:
    if _saved_rocketlib is None:
        sys.modules.pop('rocketlib', None)
    else:
        sys.modules['rocketlib'] = _saved_rocketlib
    for _name in _added:
        sys.modules.pop(_name, None)
    if _added_pkg:
        for _name in list(sys.modules):
            if _name == 'tool_gcs' or _name.startswith('tool_gcs.'):
                sys.modules.pop(_name, None)


def test_join_gcs_prefix_empty():
    assert join_gcs_prefix('', '') == ''
    assert join_gcs_prefix('', 'images') == 'images'
    assert join_gcs_prefix('', '/images/') == 'images/'


def test_join_gcs_prefix_node_only():
    assert join_gcs_prefix('data', '') == 'data/'
    assert join_gcs_prefix('data/', '') == 'data/'


def test_join_gcs_prefix_combines_and_strips_slashes():
    assert join_gcs_prefix('data', 'images') == 'data/images'
    assert join_gcs_prefix('data/', '/images/foo') == 'data/images/foo'


def _make_instance(*, prefix='data', max_download_bytes=100, blob=None, names=None):
    client = MagicMock()
    bucket = MagicMock()
    client.bucket.return_value = bucket
    if blob is not None:
        bucket.blob.return_value = blob
    if names is not None:
        bucket.list_blobs.return_value = [types.SimpleNamespace(name=n) for n in names]

    glb = IGlobal.__new__(IGlobal)
    glb.client = client
    glb.bucket_name = 'my-bucket'
    glb.prefix = prefix
    glb.max_download_bytes = max_download_bytes
    glb.temp_files = []

    inst = IInstance()
    inst.glb = glb
    return inst, client, bucket


def test_list_files_joins_node_and_runtime_prefix():
    inst, _client, bucket = _make_instance(prefix='data', names=['data/images/a.txt'])

    result = inst.list_files(prefix='/images/', max_results=5)

    assert result == ['data/images/a.txt']
    bucket.list_blobs.assert_called_once_with(prefix='data/images/', max_results=5)


def test_list_files_node_prefix_only():
    inst, _client, bucket = _make_instance(prefix='data', names=[])

    inst.list_files()

    bucket.list_blobs.assert_called_once_with(prefix='data/', max_results=10)


def test_download_file_rejects_oversize_before_fetch():
    blob = MagicMock()
    blob.size = 200
    inst, _client, bucket = _make_instance(max_download_bytes=100, blob=blob)

    result = inst.download_file('big.bin')

    assert 'error' in result
    assert 'exceeds' in result['error']
    blob.download_to_filename.assert_not_called()
    assert inst.glb.temp_files == []


def test_download_file_rejects_if_fetched_size_grows():
    blob = MagicMock()
    blob.size = 10

    def _write_large(path):
        Path(path).write_bytes(b'x' * 200)

    blob.download_to_filename.side_effect = _write_large
    inst, _client, _bucket = _make_instance(max_download_bytes=100, blob=blob)

    result = inst.download_file('swap.bin')

    assert 'error' in result
    assert 'downloaded' in result['error']
    assert inst.glb.temp_files == []
    blob.download_to_filename.assert_called_once()


def test_download_file_success_and_evicts_previous():
    blob = MagicMock()
    blob.size = 4

    def _write(path):
        Path(path).write_bytes(b'data')

    blob.download_to_filename.side_effect = _write
    inst, _client, bucket = _make_instance(prefix='data', max_download_bytes=100, blob=blob)

    first = inst.download_file('a.txt')
    assert first.get('success') is True
    first_path = first['local_path']
    assert Path(first_path).exists()
    bucket.blob.assert_called_with('data/a.txt')

    second = inst.download_file('b.txt')
    assert second.get('success') is True
    second_path = second['local_path']
    assert Path(second_path).exists()
    assert not Path(first_path).exists()
    assert inst.glb.temp_files == [second_path]

    inst.glb.endGlobal()
    assert not Path(second_path).exists()
    assert inst.glb.temp_files is None
