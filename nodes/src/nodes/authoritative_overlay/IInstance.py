from rocketlib import IInstanceBase, Entry, warning, debug
from ai.common.schema import Answer
from .IGlobal import IGlobal

from .connectors.sec import query_sec
from .connectors.ifrs import query_ifrs
from .connectors.companies_house import query_companies_house
from .connectors.edinet import query_edinet


import re

def _normalize_number(value_str: str) -> float | None:
    """Strip currency symbols, commas, and spaces, then parse to float."""
    # Remove $, €, £, ¥, commas, and spaces
    clean_str = re.sub(r'[\$€£¥,\s]', '', value_str)
    try:
        return float(clean_str)
    except ValueError:
        return None

class IInstance(IInstanceBase):
    IGlobal: IGlobal

    def __init__(self):
        super().__init__()

    def open(self, entry: Entry):
        """Reset per-object state."""
        pass

    def writeAnswers(self, answer: Answer):
        """Run authoritative cross-check on the answer.

        Extracts the answer text and attempts to verify it against the
        configured regulator database. If the official data does not match,
        the node abstains (drops the answer).
        """
        regulator_type = self.IGlobal.regulator_type
        
        # Extract text from the answer. We expect this to contain a numeric financial figure.
        text = answer.getText() if answer else ''
        text = text.strip()

        if not text:
            # Empty answer, just forward it
            self.instance.writeAnswers(answer)
            return

        normalized_text = _normalize_number(text)
        if normalized_text is None:
            warning(f"Abstaining: Could not normalize extracted text '{text}' into a number.")
            self.preventDefault()
            return

        # Query the appropriate regulator for the official number based on the snapshot.
        official_data = None
        
        try:
            if regulator_type == 'sec':
                official_data = query_sec(text)
            elif regulator_type == 'ifrs':
                official_data = query_ifrs(text)
            elif regulator_type == 'companies_house':
                official_data = query_companies_house(text)
            elif regulator_type == 'edinet':
                official_data = query_edinet(text)
            else:
                warning(f"Unknown regulator type: {regulator_type}")
                # Fail closed: abstain rather than forward an unverified answer
                self.preventDefault()
                return
        except Exception as e:
            warning(f"Failed to query {regulator_type} connector: {str(e)}")
            self.preventDefault()
            return

        if not official_data:
            warning(f"Abstaining: Extracted value '{text}' not found in {regulator_type} authoritative data.")
            self.preventDefault()
            return

        # official_data is now expected to be a list of floats
        if normalized_text not in official_data:
            warning(f"Abstaining: Value mismatch. Extracted '{text}' (normalized: {normalized_text}) does not match official data from {regulator_type}.")
            self.preventDefault()
            return

        debug(f"Authoritative Match: '{text}' verified against {regulator_type} database.")
        # Forward the answer downstream
        self.instance.writeAnswers(answer)

    def close(self):
        """Clean up on close."""
        pass
