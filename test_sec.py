import json

def query_sec(concept: str):
    with open('nodes/src/nodes/authoritative_overlay/testdata/sec_snapshot.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        values = []
        gaap = data.get('facts', {}).get('us-gaap', {})
        concept_data = gaap.get(concept)
        if concept_data:
            for unit, measurements in concept_data.get('units', {}).items():
                for measurement in measurements:
                    val = measurement.get('val')
                    if val is not None:
                        values.append(float(val))
        return values

print(query_sec("Revenues"))
