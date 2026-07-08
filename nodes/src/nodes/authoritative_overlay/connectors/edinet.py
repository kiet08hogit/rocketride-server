from . import _load_statements_snapshot

def query_edinet(concept: str, extracted_text: str):
    """Load the local EDINET snapshot for the given concept."""
    return _load_statements_snapshot(concept, 'edinet_snapshot.json', 'EDINET')
