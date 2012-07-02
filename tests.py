import json
import httplib
from hello_es import Model
from pprint import pprint

def test_message():
    model = Model()
    data = model.get_message()
    res = json.loads(str(data))
    pprint(res)
    
