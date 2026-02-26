"""
Test if the API is up and responding.
Usage: python test_api_activity.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from atclient.automate import load_api, check


def main():
    api = load_api()

    print("Testing API availability...")
    result = api.ping()

    print(f"  Timestamp     : {result['timestamp']}")
    print(f"  Available     : {result['available']}")
    print(f"  Status code   : {result['status_code']}")
    print(f"  Response time : {result['response_time_ms']} ms")

    check(result["available"], "API is up and responding.")


if __name__ == "__main__":
    main()
