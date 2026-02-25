"""
Test if the client can create a project from dataset.parquet and then clean up.
Usage: python test_api_create_project.py
"""

import random
import sys
import time
from pathlib import Path

import pandas as pd  # type: ignore

sys.path.insert(0, str(Path(__file__).parent.parent))
import atclient

CONFIG = Path(__file__).parent / "config.yaml"
DATA = Path(__file__).parent.parent / "data" / "dataset.parquet"
PROJECT_NAME = "test-create-project-" + str(random.randint(0, 1000))


def main():
    api = atclient.AtApi(config=str(CONFIG))

    df = pd.read_parquet(DATA)
    print(f"Loaded dataset: {len(df)} rows")

    print(f"Creating project '{PROJECT_NAME}'...")
    try:
        slug = api.add_project(
            project_name=PROJECT_NAME,
            data=df,
            col_id="id",
            cols_text=["text"],
            cols_label=["label"],
            n_train=1000,
            n_test=100,
            language="fr",
        )
        print(f"  Waiting 20 seconds for project to be created...")
        time.sleep(20)

        print("  Verifying project creation...")

        # Verify project appears in the list
        slugs = api.get_projects_slugs()
        if slug not in slugs:
            print(f"FAIL: project slug '{slug}' not found in project list.")
            sys.exit(1)
        print("  Project found in project list.")

        # Verify project state is accessible
        state = api.get_project_state(slug)
        n_train = state["params"]["n_train"]
        print(f"  Train set size: {n_train}")
        if n_train != 1000:
            print(f"FAIL: expected n_train=1000, got {n_train}.")
            sys.exit(1)

        print("OK: project creation successful.")

    finally:
        print(f"Cleaning up: deleting project '{PROJECT_NAME}'...")
        try:
            slugs = api.get_projects_slugs()
            if slug in slugs:
                api.delete_project(slug)
        except Exception as e:
            print(f"Warning: cleanup failed: {e}")


if __name__ == "__main__":
    main()
