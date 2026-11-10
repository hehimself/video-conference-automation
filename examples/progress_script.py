"""Choose this script in Computer Settings using your Python executable."""

import json
import time

for step in range(11):
    print(json.dumps({"type": "progress", "value": step / 10}), flush=True)
    time.sleep(0.15)
print(json.dumps({"type": "state", "state": "on"}), flush=True)
print("Example completed", flush=True)
