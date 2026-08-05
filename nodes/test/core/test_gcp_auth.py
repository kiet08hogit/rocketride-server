import pytest
import sys
from unittest.mock import patch, MagicMock

# --- Stub engine dependencies so pytest can collect without error ---
from pathlib import Path

_NODES_SRC = Path(__file__).resolve().parents[2] / 'src'
if str(_NODES_SRC) not in sys.path:
    sys.path.insert(0, str(_NODES_SRC))

_added = []
if 'depends' not in sys.modules:
    depends = MagicMock()
    depends.depends = lambda *a, **kw: None
    sys.modules['depends'] = depends
    _added.append('depends')

from nodes.core.gcp_auth import get_gcp_credentials, GCPAuthError, _DEFAULT_SCOPES

for _name in _added:
    sys.modules.pop(_name, None)
# -------------------------------------------------------------------


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
