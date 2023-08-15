#! env python
import json
import os
import subprocess
import llm

def get_local_credentials():

    keypath = subprocess.check_output( "llm keys path".split(), text=True).strip()
    print(keypath)
    with open(keypath) as f:
        return json.load(f)["openai"]


# from the docs:
model = llm.get_model("gpt-3.5-turbo")
model.key = os.environ.get("OPENAI_API_KEY", get_local_credentials())
response = model.prompt("Five surprising names for a pet pelican")
print(response.text())
