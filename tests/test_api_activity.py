"""
Test if the API is up and responding.
Usage: python test_api_activity.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import atclient

CONFIG = Path(__file__).parent / "config.yaml"


def main():
    api = atclient.AtApi(config=str(CONFIG))

    print("Testing API availability...")
    result = api.ping()

    print(f"  Timestamp     : {result['timestamp']}")
    print(f"  Available     : {result['available']}")
    print(f"  Status code   : {result['status_code']}")
    print(f"  Response time : {result['response_time_ms']} ms")

    if not result["available"]:
        print("FAIL: API is not reachable.")
        sys.exit(1)

    print("OK: API is up and responding.")


if __name__ == "__main__":
    main()
