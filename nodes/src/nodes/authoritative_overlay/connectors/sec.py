import json
import os
from rocketlib import info

def query_sec(extracted_text: str):
    """
    Simulates querying the US SEC EDGAR database by reading a local snapshot.
    Returns the loaded snapshot data, or None if not found.
    """
    snapshot_path = os.path.join(os.path.dirname(__file__), '..', 'testdata', 'sec_snapshot.json')
    try:
        with open(snapshot_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except Exception as e:
        info(f"SEC snapshot not available: {e}")
        return None
