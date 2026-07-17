import sys
import types
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch, Mock

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src' / 'nodes'))

_STUB_MODULE_NAMES = ('rocketlib', 'ai', 'ai.common', 'ai.common.config', 'ai.common.utils')


def _install_stubs() -> None:
    mod_rl = types.ModuleType('rocketlib')
    
    def mock_tool_function(*args, **kwargs):
        return lambda f: f
    
    mod_rl.tool_function = mock_tool_function
    
    class IInstanceBase:
        pass
        
    class IGlobalBase:
        pass
        
    mod_rl.IInstanceBase = IInstanceBase
    mod_rl.IGlobalBase = IGlobalBase
    mod_rl.OPEN_MODE = Mock()
    mod_rl.warning = Mock()
    sys.modules['rocketlib'] = mod_rl

    sys.modules['ai'] = types.ModuleType('ai')
    sys.modules['ai.common'] = types.ModuleType('ai.common')
    
    mod_ai_common_config = types.ModuleType('ai.common.config')
    class Config:
        pass
    mod_ai_common_config.Config = Config
    sys.modules['ai.common.config'] = mod_ai_common_config

    mod_ai_common_utils = types.ModuleType('ai.common.utils')
    mod_ai_common_utils.normalize_tool_input = lambda x, **kwargs: x
    mod_ai_common_utils.require_str = lambda x, k, **kwargs: x.get(k)
    mod_ai_common_utils.require_int = lambda x, k, **kwargs: x.get(k)
    sys.modules['ai.common.utils'] = mod_ai_common_utils


@contextmanager
def _scoped_stubs() -> Iterator[None]:
    original_modules = {module_name: sys.modules.get(module_name) for module_name in _STUB_MODULE_NAMES}
    _install_stubs()
    try:
        yield
    finally:
        for module_name, module in original_modules.items():
            if module is None:
                sys.modules.pop(module_name, None)
            else:
                sys.modules[module_name] = module


with _scoped_stubs():
    from tool_github.github_client import call, GitHubAPIError
    from tool_github.IInstance import IInstance


def test_file_get_404():
    """Test that a 404 response in file_get returns a structured dict instead of raising."""
    inst = Mock()
    inst._token.return_value = 'token'
    inst._repo.return_value = 'owner/repo'
    
    with patch('tool_github.IInstance.call') as mock_call:
        mock_call.side_effect = GitHubAPIError(404, 'Not Found')
        result = IInstance.file_get(inst, {'path': 'missing.txt'})
        assert result == {'found': False, 'message': 'GitHub API 404: Not Found'}


@patch('tool_github.github_client.time.time', return_value=1000.0)
@patch('time.sleep')
@patch('tool_github.github_client.requests.request')
def test_rate_limit_429_retry_after(mock_request, mock_sleep, mock_time):
    """Test that a 429 response with Retry-After header correctly sleeps and retries."""
    resp_429 = Mock(spec=requests.Response)
    resp_429.ok = False
    resp_429.status_code = 429
    resp_429.headers = {'Retry-After': '60'}
    resp_429.json.return_value = {'message': 'rate limit'}
    resp_429.text = 'rate limit'
    
    resp_success = Mock(spec=requests.Response)
    resp_success.ok = True
    resp_success.status_code = 200
    resp_success.json.return_value = {'success': True}
    
    mock_request.side_effect = [resp_429, resp_429, resp_success]
    
    result = call('token', 'GET', '/test')
    
    assert result == {'success': True}
    assert mock_request.call_count == 3
    assert mock_sleep.call_count == 2
    mock_sleep.assert_called_with(30.0)


@patch('tool_github.github_client.time.time', return_value=1000.0)
@patch('time.sleep')
@patch('tool_github.github_client.requests.request')
def test_rate_limit_403_reset(mock_request, mock_sleep, mock_time):
    """Test that a 403 secondary rate limit with X-RateLimit-Reset correctly sleeps and retries."""
    resp_403 = Mock(spec=requests.Response)
    resp_403.ok = False
    resp_403.status_code = 403
    resp_403.headers = {'X-RateLimit-Remaining': '0', 'X-RateLimit-Reset': '1045.0'}
    resp_403.json.return_value = {'message': 'rate limit'}
    resp_403.text = 'rate limit'
    
    mock_request.side_effect = [resp_403, resp_403, resp_403, resp_403]
    
    with pytest.raises(GitHubAPIError) as exc_info:
        call('token', 'GET', '/test')
        
    assert exc_info.value.status_code == 403
    assert mock_request.call_count == 3
    assert mock_sleep.call_count == 2
    mock_sleep.assert_called_with(30.0)
