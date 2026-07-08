import json
import os
from rocketlib import debug

def query_sec(concept: str, extracted_text: str):
    """
    Simulates querying the US SEC EDGAR database by reading a local snapshot.
    Looks up the specific concept within facts.us-gaap.
    Returns the loaded snapshot data, or None if not found.
    """
    snapshot_path = os.path.join(os.path.dirname(__file__), '..', 'testdata', 'sec_snapshot.json')
    try:
        with open(snapshot_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            values = []
            
            # Scope the lookup to the requested concept in SEC format
            gaap = data.get('facts', {}).get('us-gaap', {})
            concept_data = gaap.get(concept)
            
            if concept_data:
                # Iterate over currency units (e.g. 'USD')
                for unit, measurements in concept_data.get('units', {}).items():
                    for measurement in measurements:
                        val = measurement.get('val')
                        if val is not None:
                            try:
                                values.append(float(val))
                            except (ValueError, TypeError):
                                pass
            return values
    except FileNotFoundError:
        debug("US SEC snapshot file not found.")
        return None
    except json.JSONDecodeError:
        debug("US SEC snapshot file is invalid JSON.")
        return None
