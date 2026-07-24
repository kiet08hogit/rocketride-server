from __future__ import annotations

from ai.common.config import Config
from rocketlib import IGlobalBase, OPEN_MODE, debug, warning
from nodes.core.gcp_auth import get_gcp_credentials, GCPAuthError

try:
    from google.cloud import storage
except ImportError:
    storage = None

class IGlobal(IGlobalBase):
    """Global state for Google Cloud Storage node."""

    client: storage.Client | None = None
    bucket_name: str = ''
    prefix: str = ''

    def beginGlobal(self) -> None:
        if self.IEndpoint.endpoint.openMode == OPEN_MODE.CONFIG:
            return

        if storage is None:
            raise ImportError('google-cloud-storage is not installed.')

        cfg = Config.getNodeConfig(self.glb.logicalType, self.glb.connConfig)

        self.bucket_name = str((cfg.get('bucketName') or '')).strip()
        self.prefix = str((cfg.get('prefix') or '')).strip()

        # Auth
        try:
            creds, project_id = get_gcp_credentials(cfg)
        except Exception as e:
            warning(f'GCS authentication failed: {e}')
            raise

        self.client = storage.Client(
            project=project_id,
            credentials=creds
        )
        
        # Fail fast connection check
        try:
            if self.bucket_name:
                self.client.get_bucket(self.bucket_name)
                debug(f'tool_gcs: connected to project {self.client.project}, bucket={self.bucket_name}')
            else:
                debug(f'tool_gcs: connected to project {self.client.project} with no specific bucket configured')
        except Exception as e:
            warning(f'GCS connection check failed: {e}')
            raise

    def validateConfig(self) -> None:
        try:
            cfg = Config.getNodeConfig(self.glb.logicalType, self.glb.connConfig)
            get_gcp_credentials(cfg)
            if not str(cfg.get('bucketName') or '').strip():
                warning('bucketName is required')
        except GCPAuthError as e:
            warning(f'Auth configuration error: {e}')
        except Exception as e:
            warning(str(e))

    def endGlobal(self) -> None:
        if self.client is not None:
            self.client.close()
            self.client = None
