import sys
import json
import asyncio
from rocketride.schema.question import Answer

answer = Answer()
answer.setAnswer("{\"concept\": \"Revenues\", \"value\": \"$15,000,000\"}")
print("Answer text:", answer.getText())

answer2 = Answer(expectJson=True)
answer2.setAnswer({"concept": "Revenues", "value": "$15,000,000"})
print("Answer2 text:", answer2.getText())
