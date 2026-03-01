"""
Test if the client can start and stop model training.
Usage: python test_api_train_models.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from atclient.automate import load_api, managed_project, wait_for_training, check

BASE_MODEL = "camembert/camembert-base"


def main():
    api = load_api()

    print("Creating test project with labels...")
    with managed_project(api, force_label=True) as (slug, state):
        print(f"  Project slug: {slug}")

        # Get the scheme created from the label column
        schemes = api.get_schemes(slug)
        check(len(schemes) > 0, "Project has at least one scheme.")
        scheme = schemes[0]
        print(f"  Using scheme: {scheme}")

        # Start training
        model_name = "test-model"
        print(f"  Starting training with {BASE_MODEL}...")
        api.start_finetune_model(
            project_slug=slug,
            scheme=scheme,
            name=model_name,
            base_model=BASE_MODEL,
        )

        # Verify training started
        print("  Waiting for training to start...")
        models = wait_for_training(api, slug, timeout=30)
        check(bool(models["training"]), "Model training detected.")
        print(f"  Training models: {list(models['training'].keys())}")

        # Stop training
        print("  Stopping training...")
        api.stop_finetune_model(slug)

        check(True, "Model training start/stop lifecycle successful.")


if __name__ == "__main__":
    main()
