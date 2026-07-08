from . import _load_statements_snapshot

def query_companies_house(concept: str, extracted_text: str):
    """Load the local Companies House snapshot for the given concept."""
    return _load_statements_snapshot(concept, 'companies_house_snapshot.json', 'Companies House')
