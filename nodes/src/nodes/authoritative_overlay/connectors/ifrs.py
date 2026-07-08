from . import _load_statements_snapshot

def query_ifrs(concept: str, extracted_text: str):
    """Load the local IFRS snapshot for the given concept."""
    return _load_statements_snapshot(concept, 'ifrs_snapshot.json', 'IFRS')
