"""
Unit tests for the shared GCP credential resolver (core/gcp_auth.py).

Pure logic, no server or live API needed:

    pytest nodes/test/core/test_gcp_auth.py -v
"""

from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# core/ is a flat dir of engine-loaded modules (no __init__.py) and nodes/src is
# not on pytest's pythonpath, so import the module by adding its dir to sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src' / 'nodes' / 'core'))
from gcp_auth import GCPAuthError, _DEFAULT_SCOPES, get_gcp_credentials  # noqa: E402


def _install_google_auth_stubs() -> list[str]:
    """Make ``google.auth`` and ``google.oauth2.service_account`` patchable.

    CI's engine pytest process does not install per-node requirements, so
    google-auth is often missing. ``ROCKETRIDE_MOCK`` also ships ``google.oauth2``
    without ``google.auth``, so ``import google.auth`` fails even when oauth2
    is present.
    """
    added: list[str] = []
    google = sys.modules.get('google')
    if google is None:
        google = types.ModuleType('google')
        google.__path__ = []  # namespace package
        sys.modules['google'] = google
        added.append('google')

    if 'google.auth' not in sys.modules:
        auth = types.ModuleType('google.auth')
        auth.default = MagicMock(side_effect=Exception('Failed to find ADC'))
        sys.modules['google.auth'] = auth
        google.auth = auth
        added.append('google.auth')

    if 'google.oauth2' not in sys.modules:
        oauth2 = types.ModuleType('google.oauth2')
        oauth2.__path__ = []
        sys.modules['google.oauth2'] = oauth2
        google.oauth2 = oauth2
        added.append('google.oauth2')

    oauth2 = sys.modules['google.oauth2']
    if 'google.oauth2.service_account' not in sys.modules:
        sa = types.ModuleType('google.oauth2.service_account')

        class Credentials:
            def __init__(self, info=None, scopes=None):
                self.info = info
                self.scopes = scopes

            @classmethod
            def from_service_account_info(cls, info, scopes=None, **kwargs):
                return cls(info=info, scopes=scopes)

            def with_scopes(self, scopes):
                return Credentials(info=self.info, scopes=scopes)

        sa.Credentials = Credentials
        sys.modules['google.oauth2.service_account'] = sa
        oauth2.service_account = sa
        added.append('google.oauth2.service_account')

    return added


@pytest.fixture(autouse=True)
def _google_auth_stubs():
    added = _install_google_auth_stubs()
    try:
        yield
    finally:
        for name in reversed(added):
            sys.modules.pop(name, None)


def test_get_gcp_credentials_adc_success():
    config = {'authType': 'adc'}
    with patch('google.auth.default') as mock_default:
        mock_creds = MagicMock()
        mock_default.return_value = (mock_creds, 'my-project-id')

        creds, project_id = get_gcp_credentials(config)

        assert creds == mock_creds
        assert project_id == 'my-project-id'
        mock_default.assert_called_once_with(scopes=_DEFAULT_SCOPES)


def test_get_gcp_credentials_adc_explicit_scopes():
    config = {'authType': 'adc'}
    scopes = ['https://www.googleapis.com/auth/datastore']
    with patch('google.auth.default') as mock_default:
        mock_creds = MagicMock()
        mock_default.return_value = (mock_creds, 'my-project-id')

        creds, project_id = get_gcp_credentials(config, scopes=scopes)

        assert creds == mock_creds
        assert project_id == 'my-project-id'
        mock_default.assert_called_once_with(scopes=scopes)


def test_get_gcp_credentials_adc_explicit_project():
    config = {'authType': 'adc', 'projectId': 'explicit-project'}
    with patch('google.auth.default') as mock_default:
        mock_creds = MagicMock()
        mock_default.return_value = (mock_creds, 'my-project-id')

        creds, project_id = get_gcp_credentials(config)

        assert creds == mock_creds
        assert project_id == 'explicit-project'


def test_get_gcp_credentials_adc_failure():
    config = {'authType': 'adc'}
    with patch('google.auth.default', side_effect=Exception('Failed to find ADC')):
        with pytest.raises(GCPAuthError, match='Failed to acquire Application Default Credentials'):
            get_gcp_credentials(config)


def test_get_gcp_credentials_service_account_missing_key():
    config = {'authType': 'service_account'}
    with pytest.raises(GCPAuthError, match='Service Account JSON key is required'):
        get_gcp_credentials(config)


def test_get_gcp_credentials_service_account_invalid_json():
    config = {'authType': 'service_account', 'serviceAccountKey': 'not-a-json'}
    with pytest.raises(GCPAuthError, match='Failed to parse Service Account JSON key'):
        get_gcp_credentials(config)


@patch('google.oauth2.service_account.Credentials.from_service_account_info')
def test_get_gcp_credentials_service_account_success_raw_json(mock_from_info):
    mock_creds = MagicMock()
    mock_scoped = MagicMock()
    mock_creds.with_scopes.return_value = mock_scoped
    mock_from_info.return_value = mock_creds

    config = {
        'authType': 'service_account',
        'serviceAccountKey': '{"project_id": "test-project", "client_email": "test@example.com"}',
    }

    creds, project_id = get_gcp_credentials(config)

    assert creds == mock_scoped
    assert project_id == 'test-project'
    mock_from_info.assert_called_once_with({'project_id': 'test-project', 'client_email': 'test@example.com'})
    mock_creds.with_scopes.assert_called_once_with(_DEFAULT_SCOPES)


@patch('google.oauth2.service_account.Credentials.from_service_account_info')
def test_get_gcp_credentials_service_account_success_data_url(mock_from_info):
    mock_creds = MagicMock()
    mock_scoped = MagicMock()
    mock_creds.with_scopes.return_value = mock_scoped
    mock_from_info.return_value = mock_creds

    # {"project_id": "test-project-b64"} base64 encoded
    b64_json = 'eyJwcm9qZWN0X2lkIjogInRlc3QtcHJvamVjdC1iNjQifQ=='

    config = {'authType': 'service_account', 'serviceAccountKey': f'data:application/json;base64,{b64_json}'}

    creds, project_id = get_gcp_credentials(config)

    assert creds == mock_scoped
    assert project_id == 'test-project-b64'
    mock_from_info.assert_called_once_with({'project_id': 'test-project-b64'})
    mock_creds.with_scopes.assert_called_once_with(_DEFAULT_SCOPES)


@patch('google.oauth2.service_account.Credentials.from_service_account_info')
def test_get_gcp_credentials_service_account_explicit_scopes(mock_from_info):
    mock_creds = MagicMock()
    mock_scoped = MagicMock()
    mock_creds.with_scopes.return_value = mock_scoped
    mock_from_info.return_value = mock_creds

    scopes = ['https://www.googleapis.com/auth/datastore']
    config = {'authType': 'service_account', 'serviceAccountKey': '{"project_id": "test-project"}'}

    creds, project_id = get_gcp_credentials(config, scopes=scopes)

    assert creds == mock_scoped
    assert project_id == 'test-project'
    mock_creds.with_scopes.assert_called_once_with(scopes)


def test_get_gcp_credentials_unknown_auth_type():
    config = {'authType': 'bogus'}
    with pytest.raises(GCPAuthError, match='Unknown authType'):
        get_gcp_credentials(config)


def test_config_errors_do_not_require_google_auth():
    """Cheap config errors must not depend on google-auth being importable.

    CI pytest does not install per-node requirements, and ROCKETRIDE_MOCK's
    google package has oauth2 but no auth submodule.
    """
    saved = {
        name: sys.modules.pop(name) for name in list(sys.modules) if name == 'google' or name.startswith('google.')
    }
    try:
        with pytest.raises(GCPAuthError, match='Unknown authType'):
            get_gcp_credentials({'authType': 'bogus'})
        with pytest.raises(GCPAuthError, match='Service Account JSON key is required'):
            get_gcp_credentials({'authType': 'service_account'})
        with pytest.raises(GCPAuthError, match='Failed to parse Service Account JSON key'):
            get_gcp_credentials({'authType': 'service_account', 'serviceAccountKey': 'not-a-json'})
    finally:
        sys.modules.update(saved)
