from ai.common.tool import tool_function
from rocketlib import IInstanceBase
from typing import List, Dict, Any

class IInstance(IInstanceBase):
    """Vertex AI Vector Search instance."""

    @tool_function(
        description='Search for nearest neighbors in Vertex AI Vector Search.',
        args={
            'query_vector': 'A list of floats representing the query embedding.',
            'top_k': 'Number of nearest neighbors to return.',
            'score_threshold': 'Optional minimum distance score to return.'
        }
    )
    def search(self, query_vector: List[float], top_k: int = 10, score_threshold: float = 0.0) -> List[Dict[str, Any]]:
        index_endpoint = self.glb.index_endpoint
        if not index_endpoint:
            return [{'error': 'Vertex AI Index Endpoint is not connected.'}]
            
        try:
            response = index_endpoint.find_neighbors(
                deployed_index_id=self.glb.deployed_index_id,
                queries=[query_vector],
                num_neighbors=top_k
            )
            
            results = []
            if response and len(response) > 0:
                for neighbor in response[0]:
                    if score_threshold > 0.0 and neighbor.distance < score_threshold:
                        continue
                    
                    results.append({
                        'id': neighbor.id,
                        'distance': neighbor.distance
                    })
            return results
        except Exception as e:
            return [{'error': f'Failed to search Vertex AI: {e}'}]
