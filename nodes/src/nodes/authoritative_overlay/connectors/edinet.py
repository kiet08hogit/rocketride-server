import json
import os
from rocketlib import info

def query_edinet(extracted_text: str):
    snapshot_path = os.path.join(os.path.dirname(__file__), '..', 'testdata', 'edinet_snapshot.json')
    try:
        with open(snapshot_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        info(f"EDINET snapshot not available: {e}")
        return None
