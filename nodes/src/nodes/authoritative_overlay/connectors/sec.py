import json
import os
from rocketlib import debug

def query_sec(extracted_text: str):
    """
    Simulates querying the US SEC EDGAR database by reading a local snapshot.
    Returns the loaded snapshot data, or None if not found.
    """
    snapshot_path = os.path.join(os.path.dirname(__file__), '..', 'testdata', 'sec_snapshot.json')
    try:
        with open(snapshot_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            values = []
            facts = data.get('facts', {}).get('us-gaap', {})
            for concept in facts.values():
                for unit_list in concept.get('units', {}).values():
                    for item in unit_list:
                        if 'val' in item:
                            try:
                                values.append(float(item['val']))
                            except (ValueError, TypeError):
                                pass
            return values
    except Exception as e:
        debug(f'SEC snapshot not available: {e}')
        return None
