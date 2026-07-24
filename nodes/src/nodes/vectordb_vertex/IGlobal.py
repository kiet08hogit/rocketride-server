from __future__ import annotations

from ai.common.config import Config
from rocketlib import IGlobalBase, OPEN_MODE, debug, warning
from nodes.core.gcp_auth import get_gcp_credentials, GCPAuthError

try:
    from google.cloud import aiplatform
except ImportError:
    aiplatform = None

class IGlobal(IGlobalBase):
    """Global state for Vertex AI Vector Search node."""

    index_endpoint = None
    deployed_index_id: str = ''
    location: str = 'us-central1'
    project_id: str = ''

    def beginGlobal(self) -> None:
        if self.IEndpoint.endpoint.openMode == OPEN_MODE.CONFIG:
            return

        if aiplatform is None:
            raise ImportError('google-cloud-aiplatform is not installed.')

        cfg = Config.getNodeConfig(self.glb.logicalType, self.glb.connConfig)

        self.location = str((cfg.get('location') or 'us-central1')).strip()
        index_endpoint_id = str((cfg.get('indexEndpointId') or '')).strip()
        self.deployed_index_id = str((cfg.get('deployedIndexId') or '')).strip()

        if not index_endpoint_id or not self.deployed_index_id:
            warning('indexEndpointId and deployedIndexId are required for Vertex AI Vector Search.')

        # Auth
        try:
            creds, self.project_id = get_gcp_credentials(cfg)
        except Exception as e:
            warning(f'Vertex AI authentication failed: {e}')
            raise

        aiplatform.init(
            project=self.project_id,
            location=self.location,
            credentials=creds
        )
        
        # Connect to Index Endpoint
        try:
            if index_endpoint_id:
                self.index_endpoint = aiplatform.MatchingEngineIndexEndpoint(
                    index_endpoint_name=index_endpoint_id
                )
                debug(f'vectordb_vertex: connected to index endpoint {index_endpoint_id}')
        except Exception as e:
            warning(f'Vertex AI connection check failed: {e}')
            raise

    def validateConfig(self) -> None:
        try:
            cfg = Config.getNodeConfig(self.glb.logicalType, self.glb.connConfig)
            get_gcp_credentials(cfg)
            if not str(cfg.get('indexEndpointId') or '').strip():
                warning('indexEndpointId is required')
            if not str(cfg.get('deployedIndexId') or '').strip():
                warning('deployedIndexId is required')
        except GCPAuthError as e:
            warning(f'Auth configuration error: {e}')
        except Exception as e:
            warning(str(e))

    def endGlobal(self) -> None:
        self.index_endpoint = None
