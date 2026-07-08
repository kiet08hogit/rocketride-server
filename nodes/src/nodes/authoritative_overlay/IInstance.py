from rocketlib import IInstanceBase, Entry, warning, debug
from ai.common.schema import Answer
from .IGlobal import IGlobal

from .connectors.sec import query_sec
from .connectors.ifrs import query_ifrs
from .connectors.companies_house import query_companies_house
from .connectors.edinet import query_edinet


import re
import json

def _normalize_number(value_str: str) -> float | None:
    """Strip currency symbols, commas, and spaces, then parse to float.
    Handles parenthesized negatives and scale suffixes (M, k, B, in thousands).
    """
    clean_str = value_str.strip().lower()
    
    # Handle "in thousands", "in millions", etc.
    scale = 1.0
    if 'in thousands' in clean_str:
        scale = 1_000.0
        clean_str = clean_str.replace('in thousands', '')
    elif 'in millions' in clean_str:
        scale = 1_000_000.0
        clean_str = clean_str.replace('in millions', '')
    elif 'in billions' in clean_str:
        scale = 1_000_000_000.0
        clean_str = clean_str.replace('in billions', '')
        
    # Remove currency, commas, and spaces
    clean_str = re.sub(r'[\$€£¥,\s]', '', clean_str)
    
    # Handle k, m, b suffixes
    if clean_str.endswith('k'):
        scale *= 1_000.0
        clean_str = clean_str[:-1]
    elif clean_str.endswith('m'):
        scale *= 1_000_000.0
        clean_str = clean_str[:-1]
    elif clean_str.endswith('b'):
        scale *= 1_000_000_000.0
        clean_str = clean_str[:-1]
        
    # Handle parenthesized negatives: (1.5) -> -1.5
    if clean_str.startswith('(') and clean_str.endswith(')'):
        clean_str = '-' + clean_str[1:-1]
        
    try:
        return float(clean_str) * scale
    except ValueError:
        return None

class IInstance(IInstanceBase):
    IGlobal: IGlobal

    def __init__(self):
        super().__init__()

    def open(self, entry: Entry):
        """Reset per-object state."""
        pass

    def writeText(self, text: str):
        """Handle raw text input (used by the test framework).

        The test framework sends data on the ``text`` lane as a plain
        string.  This handler parses the JSON payload, constructs a
        proper ``Answer`` object, and delegates to ``writeAnswers``.
        """
        text = text.strip()
        if not text:
            warning("Abstaining: empty text received.")
            self.preventDefault()
            return

        # Build a real Answer so the rest of the pipeline sees the same type
        answer = Answer()
        answer.setAnswer(text)
        self.writeAnswers(answer)

    def writeAnswers(self, answer: Answer):
        """Run authoritative cross-check on the answer.

        Extracts the answer text and attempts to verify it against the
        configured regulator database. If the official data does not match,
        the node abstains (drops the answer).
        """
        regulator_type = self.IGlobal.regulator_type
        
        # We expect a JSON answer with a 'concept' and a 'value'
        try:
            payload = None
            text_val = answer.getText()
            
            if answer.isJson():
                payload = answer.getJson()
            else:
                if isinstance(text_val, dict):
                    payload = text_val
                else:
                    payload = json.loads(text_val)
                    
            if not isinstance(payload, dict):
                raise ValueError(f"Payload is not a dictionary, it is {type(payload)}")
                
            concept = payload.get('concept', '')
            text = str(payload.get('value', ''))
        except Exception as e:
            warning(f"Abstaining: Expected JSON answer with 'concept' and 'value'. Error: {e}")
            self.preventDefault()
            return
            
        text = text.strip()
        concept = concept.strip()

        if not text or not concept:
            warning("Abstaining: Missing concept or value in answer.")
            self.preventDefault()
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
                official_data = query_sec(concept, text)
            elif regulator_type == 'ifrs':
                official_data = query_ifrs(concept, text)
            elif regulator_type == 'companies_house':
                official_data = query_companies_house(concept, text)
            elif regulator_type == 'edinet':
                official_data = query_edinet(concept, text)
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
