import json
text = "{\"concept\": \"Revenues\", \"value\": \"$15,000,000\"}"
print("Text:", text)
payload = json.loads(text)
print("Payload:", payload)
