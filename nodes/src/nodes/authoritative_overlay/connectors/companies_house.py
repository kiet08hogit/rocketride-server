import json
import os
from rocketlib import info

def query_companies_house(extracted_text: str):
    snapshot_path = os.path.join(os.path.dirname(__file__), '..', 'testdata', 'companies_house_snapshot.json')
    try:
        with open(snapshot_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        info(f"Companies House snapshot not available: {e}")
        return None
