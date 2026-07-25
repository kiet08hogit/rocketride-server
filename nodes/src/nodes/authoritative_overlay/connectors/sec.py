# =============================================================================
# MIT License
# Copyright (c) 2026 Aparavi Software AG
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# =============================================================================

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
        debug('US SEC snapshot file not found')
        return None
    except json.JSONDecodeError:
        debug('US SEC snapshot file is invalid JSON')
        return None
