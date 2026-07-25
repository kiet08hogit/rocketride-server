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

# Connectors for authoritative overlay

import json
import os
from rocketlib import debug

def _load_statements_snapshot(concept: str, snapshot_filename: str, log_name: str) -> list[float] | None:
    """Helper to load a specific concept from a statements snapshot."""
    snapshot_path = os.path.join(os.path.dirname(__file__), '..', 'testdata', snapshot_filename)
    try:
        with open(snapshot_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            values = []
            
            # Scope the lookup to the requested concept
            statements = data.get('statements', {})
            val = statements.get(concept)
            
            if val is not None:
                try:
                    values.append(float(val))
                except (ValueError, TypeError):
                    pass
            return values
    except Exception as e:
        debug(f'{log_name} snapshot not available: {e}')
        return None
