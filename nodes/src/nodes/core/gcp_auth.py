import base64
import json
from typing import Optional, Tuple, Any

# Default scope when callers omit one. Service-account credentials require an
# explicit scope set; without it google-auth leaves requires_scopes=True and
# client refresh fails. ADC also accepts this when passed to google.auth.default.
_DEFAULT_SCOPES = ['https://www.googleapis.com/auth/cloud-platform']


class GCPAuthError(Exception):
    """Raised when GCP authentication fails or config is invalid."""

    pass


def _missing_google_auth() -> GCPAuthError:
    return GCPAuthError("google-auth library is not installed. Ensure node requirements include 'google-auth'.")


def get_gcp_credentials(config: dict, scopes: Optional[list[str]] = None) -> Tuple[Any, Optional[str]]:
    """
    Resolves GCP credentials from the given node configuration.

    Returns:
        tuple[google.auth.credentials.Credentials, str]: The credentials and the resolved project ID.

    Raises:
        GCPAuthError: If configuration is invalid or missing.
    """
    resolved_scopes = list(scopes) if scopes else list(_DEFAULT_SCOPES)
    auth_type = config.get('authType', 'adc')
    project_id = config.get('projectId')

    if auth_type == 'service_account':
        key_data = config.get('serviceAccountKey')
        if not key_data:
            raise GCPAuthError("Service Account JSON key is required when authType is 'service_account', but missing.")

        # RocketRide UI usually uploads files as base64 data-url: data:application/json;base64,...
        try:
            if key_data.startswith('data:'):
                _, b64_data = key_data.split(',', 1)
                json_bytes = base64.b64decode(b64_data)
                key_info = json.loads(json_bytes.decode('utf-8'))
            else:
                # Fallback if raw JSON string is passed directly
                key_info = json.loads(key_data)
        except Exception as e:
            raise GCPAuthError(f'Failed to parse Service Account JSON key: {e}')

        try:
            from google.oauth2 import service_account
        except ImportError:
            raise _missing_google_auth()

        try:
            creds = service_account.Credentials.from_service_account_info(key_info)
            creds = creds.with_scopes(resolved_scopes)
        except Exception as e:
            raise GCPAuthError(f'Invalid Service Account format: {e}')

        if not project_id:
            project_id = key_info.get('project_id')

        return creds, project_id

    elif auth_type == 'adc':
        try:
            import google.auth
        except ImportError:
            raise _missing_google_auth()
        try:
            creds, default_project_id = google.auth.default(scopes=resolved_scopes)
            if not project_id:
                project_id = default_project_id
            return creds, project_id
        except Exception as e:
            raise GCPAuthError(f'Failed to acquire Application Default Credentials: {e}')

    else:
        raise GCPAuthError(f'Unknown authType: {auth_type}')
