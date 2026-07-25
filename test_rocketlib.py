import sys
sys.path.insert(0, './packages/server/engine-lib/rocketlib-python/lib')
from rocketlib.schema.question import Answer

a = Answer()
a.setAnswer("hello")
print("a:", a.getText())
