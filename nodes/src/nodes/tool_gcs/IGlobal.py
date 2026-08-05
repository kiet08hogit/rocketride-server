from __future__ import annotations

import os
from typing import List

from ai.common.config import Config
from rocketlib import IGlobalBase, OPEN_MODE, debug, warning

try:
    from google.cloud import storage
except ImportError:
    storage = None

_GCS_SCOPES = ['https://www.googleapis.com/auth/devstorage.read_only']
# 50 MiB default download cap — keeps agents from filling server disk.
_DEFAULT_MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024


class IGlobal(IGlobalBase):
    """Global state for Google Cloud Storage node."""

    client: storage.Client | None = None
    bucket_name: str = ''
    prefix: str = ''
    max_download_bytes: int = _DEFAULT_MAX_DOWNLOAD_BYTES
    temp_files: List[str] | None = None

    def beginGlobal(self) -> None:
        if self.IEndpoint.endpoint.openMode == OPEN_MODE.CONFIG:
            return

        if storage is None:
            raise ImportError('google-cloud-storage is not installed.')

        # deferred: engine-path import
        from nodes.core.gcp_auth import get_gcp_credentials

        cfg = Config.getNodeConfig(self.glb.logicalType, self.glb.connConfig)

        self.bucket_name = str((cfg.get('bucketName') or '')).strip()
        self.prefix = str((cfg.get('prefix') or '')).strip()
        try:
            max_bytes = int(cfg.get('maxDownloadBytes') or _DEFAULT_MAX_DOWNLOAD_BYTES)
        except (TypeError, ValueError):
            max_bytes = _DEFAULT_MAX_DOWNLOAD_BYTES
        self.max_download_bytes = max(1, max_bytes)
        self.temp_files = []

        # Auth
        try:
            creds, project_id = get_gcp_credentials(cfg, scopes=_GCS_SCOPES)
        except Exception as e:
            warning(f'GCS authentication failed: {e}')
            raise

        self.client = storage.Client(project=project_id, credentials=creds)

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
        # deferred: engine-path import
        from nodes.core.gcp_auth import get_gcp_credentials, GCPAuthError

        try:
            cfg = Config.getNodeConfig(self.glb.logicalType, self.glb.connConfig)
            get_gcp_credentials(cfg, scopes=_GCS_SCOPES)
            if not str(cfg.get('bucketName') or '').strip():
                warning('bucketName is required')
        except GCPAuthError as e:
            warning(f'Auth configuration error: {e}')
        except Exception as e:
            warning(str(e))

    def endGlobal(self) -> None:
        for path in list(self.temp_files or []):
            try:
                if path and os.path.exists(path):
                    os.remove(path)
            except OSError as e:
                warning(f'tool_gcs: failed to remove temp file {path}: {e}')
        self.temp_files = None

        if self.client is not None:
            self.client.close()
            self.client = None
