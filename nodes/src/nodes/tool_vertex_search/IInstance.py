from __future__ import annotations

from typing import Any

from rocketlib import IInstanceBase, tool_function

from .IGlobal import IGlobal


def _as_dict(args: Any) -> dict:
    return args if isinstance(args, dict) else {}


class IInstance(IInstanceBase):
    """Vertex AI Vector Search instance."""

    IGlobal: IGlobal

    @tool_function(
        description=(
            'Search for nearest neighbors in Vertex AI Vector Search. '
            'score_threshold assumes similarity semantics (higher is better), e.g. '
            'DOT_PRODUCT_DISTANCE; it is not correct for SQUARED_L2_DISTANCE.'
        ),
        input_schema={
            'type': 'object',
            'required': ['query_vector'],
            'properties': {
                'query_vector': {
                    'type': 'array',
                    'items': {'type': 'number'},
                    'description': 'A list of floats representing the query embedding.',
                },
                'top_k': {
                    'type': 'integer',
                    'description': 'Number of nearest neighbors to return.',
                },
                'score_threshold': {
                    'type': 'number',
                    'description': (
                        'Optional minimum similarity score to keep. Neighbors with a lower '
                        'distance/score are dropped. Assumes similarity metrics (higher better); '
                        'do not use with L2 distance indexes.'
                    ),
                },
            },
        },
    )
    def search(self, args: dict | None = None) -> list[dict[str, Any]]:
        """Return nearest neighbors for ``query_vector``.

        Args:
            args: Tool arguments with ``query_vector``, optional ``top_k``,
                and optional ``score_threshold``.

        Returns:
            A list of ``{id, distance}`` dicts, or a one-item list with
            ``error`` when the endpoint is disconnected or the search fails.
        """
        args = _as_dict(args)
        query_vector = args.get('query_vector') or []
        try:
            top_k = int(args.get('top_k') or 10)
        except (TypeError, ValueError):
            top_k = 10
        try:
            score_threshold = float(args.get('score_threshold') or 0.0)
        except (TypeError, ValueError):
            score_threshold = 0.0

        index_endpoint = self.IGlobal.index_endpoint
        if not index_endpoint:
            return [{'error': 'Vertex AI Index Endpoint is not connected.'}]

        try:
            response = index_endpoint.find_neighbors(
                deployed_index_id=self.IGlobal.deployed_index_id, queries=[query_vector], num_neighbors=top_k
            )

            results = []
            if response and len(response) > 0:
                for neighbor in response[0]:
                    if score_threshold > 0.0 and neighbor.distance < score_threshold:
                        continue

                    results.append({'id': neighbor.id, 'distance': neighbor.distance})
            return results
        except Exception as e:
            return [{'error': f'Failed to search Vertex AI: {e}'}]
