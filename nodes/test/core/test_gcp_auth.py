import pytest
import sys
from unittest.mock import patch, MagicMock

# --- Stub engine dependencies so pytest can collect without error ---
from pathlib import Path
_NODES_SRC = Path(__file__).resolve().parents[3] / 'src'
if str(_NODES_SRC) not in sys.path:
    sys.path.insert(0, str(_NODES_SRC))

_added = []
if 'depends' not in sys.modules:
    depends = MagicMock()
    depends.depends = lambda *a, **kw: None
    sys.modules['depends'] = depends
    _added.append('depends')

from nodes.core.gcp_auth import get_gcp_credentials, GCPAuthError

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
        mock_default.assert_called_once()

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
    mock_from_info.return_value = mock_creds
    
    config = {
        'authType': 'service_account', 
        'serviceAccountKey': '{"project_id": "test-project"}'
    }
    
    creds, project_id = get_gcp_credentials(config)
    
    assert creds == mock_creds
    assert project_id == 'test-project'
    mock_from_info.assert_called_once_with({'project_id': 'test-project'})

@patch('google.oauth2.service_account.Credentials.from_service_account_info')
def test_get_gcp_credentials_service_account_success_data_url(mock_from_info):
    mock_creds = MagicMock()
    mock_from_info.return_value = mock_creds
    
    # {"project_id": "test-project-b64"} base64 encoded
    b64_json = 'eyJwcm9qZWN0X2lkIjogInRlc3QtcHJvamVjdC1iNjQifQ=='
    
    config = {
        'authType': 'service_account', 
        'serviceAccountKey': f'data:application/json;base64,{b64_json}'
    }
    
    creds, project_id = get_gcp_credentials(config)
    
    assert creds == mock_creds
    assert project_id == 'test-project-b64'
    mock_from_info.assert_called_once_with({'project_id': 'test-project-b64'})
