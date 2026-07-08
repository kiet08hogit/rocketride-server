import json
import os
from rocketlib import debug

def query_ifrs(extracted_text: str):
    """Load the local IFRS snapshot, returning None on failure."""
    snapshot_path = os.path.join(os.path.dirname(__file__), '..', 'testdata', 'ifrs_snapshot.json')
    try:
        with open(snapshot_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            values = []
            for v in data.get('statements', {}).values():
                try:
                    values.append(float(v))
                except (ValueError, TypeError):
                    pass
            return values
    except Exception as e:
        debug(f'IFRS snapshot not available: {e}')
        return None
