"""
Test if the client can create a project from dataset.parquet and then clean up.
Usage: python test_api_create_project.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from atclient.automate import load_api, managed_project, check


def main():
    api = load_api()

    print("Creating test project...")
    with managed_project(api, n_train=1000, n_test=100) as (slug, state):
        print(f"  Project slug: {slug}")

        # Verify project appears in the list
        slugs = api.get_projects_slugs()
        check(slug in slugs, "Project found in project list.")

        # Verify project state
        n_train = state["params"]["n_train"]
        print(f"  Train set size: {n_train}")
        check(n_train == 1000, "Project n_train matches expected value.")

        print("OK: project creation successful.")


if __name__ == "__main__":
    main()
