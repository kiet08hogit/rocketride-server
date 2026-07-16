from __future__ import annotations

from ai.common.config import Config
from rocketlib import IGlobalBase, OPEN_MODE, debug, warning
from nodes.core.gcp_auth import get_gcp_credentials, GCPAuthError

try:
    from google.cloud import firestore
except ImportError:
    firestore = None

class IGlobal(IGlobalBase):
    """Global state for Firestore node."""

    client: firestore.Client | None = None
    database: str = '(default)'
    collection: str = ''

    def beginGlobal(self) -> None:
        if self.IEndpoint.endpoint.openMode == OPEN_MODE.CONFIG:
            return

        if firestore is None:
            raise ImportError("google-cloud-firestore is not installed.")

        cfg = Config.getNodeConfig(self.glb.logicalType, self.glb.connConfig)

        self.database = str((cfg.get('database') or '(default)')).strip() or '(default)'
        self.collection = str((cfg.get('collection') or '')).strip()

        # Auth
        try:
            creds, project_id = get_gcp_credentials(cfg)
        except Exception as e:
            warning(f"Firestore authentication failed: {e}")
            raise

        self.client = firestore.Client(
            project=project_id,
            credentials=creds,
            database=self.database
        )
        
        # Fail fast connection check
        try:
            # simple check to verify connectivity/auth
            next(self.client.collections(page_size=1), None)
            debug(f'db_firestore: connected to project {self.client.project}, database={self.database}')
        except Exception as e:
            warning(f"Firestore connection check failed: {e}")
            raise

    def validateConfig(self) -> None:
        try:
            cfg = Config.getNodeConfig(self.glb.logicalType, self.glb.connConfig)
            get_gcp_credentials(cfg) # Validates credentials parse successfully
            if not str(cfg.get('collection') or '').strip():
                warning('collection is recommended')
        except GCPAuthError as e:
            warning(f"Auth configuration error: {e}")
        except Exception as e:
            warning(str(e))

    def endGlobal(self) -> None:
        if self.client is not None:
            self.client.close()
            self.client = None
