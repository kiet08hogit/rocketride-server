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
import requests
from rocketlib import debug, warning

def query_sec(concept: str, extracted_text: str, cik: str):
    """
    Queries the US SEC EDGAR API for a specific concept within us-gaap.
    Returns a list of values found, or None if the query fails.
    """
    if not cik:
        warning('SEC EDGAR requires a CIK.')
        return None

    url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{concept}.json"
    headers = {
        'User-Agent': 'RocketRide-Authoritative-Overlay/1.0'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 404:
            debug(f'US SEC concept {concept} not found for CIK {cik}')
            return None
            
        response.raise_for_status()
        data = response.json()
        
        values = []
        for unit, measurements in data.get('units', {}).items():
            for measurement in measurements:
                val = measurement.get('val')
                if val is not None:
                    try:
                        values.append(float(val))
                    except (ValueError, TypeError):
                        pass
        return values
    except requests.exceptions.RequestException as e:
        warning(f'US SEC API query failed: {str(e)}')
        return None
