from rocketride.schema.question import Answer

a = Answer(**{"text": "$15,000,000"})
print("a:", a.answer)

b = Answer(**{"answer": "$15,000,000"})
print("b:", b.answer)
