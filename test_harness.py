import json

class Answer:
    def __init__(self, text="", expectJson=False):
        self._text = text
        self._expectJson = expectJson
    
    def isJson(self):
        return self._expectJson
        
    def getText(self):
        return self._text

def parse(answer):
    try:
        # First try getJson() if upstream explicitly sent JSON
        payload = None
        if answer.isJson():
            payload = answer.getJson()
        else:
            text_val = answer.getText()
            if isinstance(text_val, dict):
                payload = text_val
            else:
                payload = json.loads(text_val)
                
        if not isinstance(payload, dict):
            raise ValueError("Payload is not a dictionary")
            
        concept = payload.get('concept', '')
        text = str(payload.get('value', ''))
        return concept, text
    except Exception as e:
        return f"Error: {e}"

ans1 = Answer("{\"concept\": \"Revenues\", \"value\": \"$15,000,000\"}")
print(parse(ans1))

# What if answer text is passed as a dict in the test mock?
ans2 = Answer({"concept": "Revenues", "value": "$15,000,000"})
print(parse(ans2))

