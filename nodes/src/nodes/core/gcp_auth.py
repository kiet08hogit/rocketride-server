import base64
import json
from typing import Optional, Tuple, Any

class GCPAuthError(Exception):
    """Raised when GCP authentication fails or config is invalid."""

    pass

def get_gcp_credentials(config: dict, scopes: Optional[list[str]] = None) -> Tuple[Any, Optional[str]]:
    """
    Resolves GCP credentials from the given node configuration.
    
    Returns:
        tuple[google.auth.credentials.Credentials, str]: The credentials and the resolved project ID.
        
    Raises:
        GCPAuthError: If configuration is invalid or missing.
    """
    try:
        import google.auth
        from google.oauth2 import service_account
    except ImportError:
        raise GCPAuthError("google-auth library is not installed. Ensure node requirements include 'google-auth'.")

    auth_type = config.get('authType', 'adc')
    project_id = config.get('projectId')

    if auth_type == 'service_account':
        key_data = config.get('serviceAccountKey')
        if not key_data:
            raise GCPAuthError("Service Account JSON key is required when authType is 'service_account', but missing.")
        
        # RocketRide UI usually uploads files as base64 data-url: data:application/json;base64,...
        try:
            if ',' in key_data:
                _, b64_data = key_data.split(',', 1)
                json_bytes = base64.b64decode(b64_data)
                key_info = json.loads(json_bytes.decode('utf-8'))
            else:
                # Fallback if raw JSON string is passed directly
                key_info = json.loads(key_data)
        except Exception as e:
            raise GCPAuthError(f'Failed to parse Service Account JSON key: {e}')

        try:
            creds = service_account.Credentials.from_service_account_info(key_info)
            if scopes:
                creds = creds.with_scopes(scopes)
        except Exception as e:
            raise GCPAuthError(f'Invalid Service Account format: {e}')
        
        if not project_id:
            project_id = key_info.get('project_id')
            
        return creds, project_id

    elif auth_type == 'adc':
        # Application Default Credentials
        try:
            creds, default_project_id = google.auth.default(scopes=scopes)
            if not project_id:
                project_id = default_project_id
            return creds, project_id
        except Exception as e:
            raise GCPAuthError(f'Failed to acquire Application Default Credentials: {e}')

    else:
        raise GCPAuthError(f'Unknown gcp.authType: {auth_type}')
