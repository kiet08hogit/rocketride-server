# Connectors for authoritative overlay

import json
import os
from rocketlib import debug

def _load_statements_snapshot(concept: str, snapshot_filename: str, log_name: str) -> list[float] | None:
    """Helper to load a specific concept from a statements snapshot."""
    snapshot_path = os.path.join(os.path.dirname(__file__), '..', 'testdata', snapshot_filename)
    try:
        with open(snapshot_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            values = []
            
            # Scope the lookup to the requested concept
            statements = data.get('statements', {})
            val = statements.get(concept)
            
            if val is not None:
                try:
                    values.append(float(val))
                except (ValueError, TypeError):
                    pass
            return values
    except Exception as e:
        debug(f'{log_name} snapshot not available: {e}')
        return None
