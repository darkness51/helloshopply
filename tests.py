import json
import httplib
from hello_es import Model
from pprint import pprint

def test_message():
    model = Model()
    data = model.get_message().get("allinfo")
    assert data[u"status"] == 200
    assert data[u"ok"] == True
    
