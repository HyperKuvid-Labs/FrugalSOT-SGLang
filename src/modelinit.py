import json
import sys
import os

def modelsInitialization():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "config.json")
    with open(config_path, 'r') as f:
        data = json.load(f)

    config = data["models"]

    print(json.dumps(config))

if __name__ == "__main__":
    modelsInitialization()