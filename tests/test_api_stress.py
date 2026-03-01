"""
Stress benchmark: create N users, each creates a project and starts BERT training.
Runs for T minutes then tears everything down.

Usage: python test_api_stress.py [--users N] [--duration T]
  N: number of concurrent users (default: 5)
  T: duration in minutes (default: 10)
"""

import argparse
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from atclient.automate import (
    check,
    create_test_project,
    create_test_user,
    delete_test_project,
    delete_test_user,
    load_api,
    load_test_data,
    wait_for_training,
)
from atclient.pyactivetigger import AtApi

BASE_MODEL = "camembert/camembert-base"
USER_PASSWORD = "Stresstest1!"


def worker(admin_api, user_index, data, results, ready_event, stop_event):
    """Single user workload: create project, start BERT training, wait."""
    tag = f"[user-{user_index}]"
    username = None
    user_api = None
    slug = None

    try:
        # 1. Admin creates a user account
        username = create_test_user(
            admin_api, prefix=f"stress{user_index}", password=USER_PASSWORD
        )
        print(f"{tag} Created user: {username}")
        results[user_index]["username"] = username

        # 2. User connects with their own session
        user_api = AtApi(url=admin_api.url)
        user_api.connect(username, USER_PASSWORD)
        if user_api.headers is None:
            raise Exception(f"{tag} User authentication failed")
        print(f"{tag} Authenticated")

        # 3. User creates a project with labels
        print(f"{tag} Creating project...")
        slug, state = create_test_project(
            user_api, data=data, force_label=True, n_train=500, n_test=50, timeout=120
        )
        print(f"{tag} Project ready: {slug}")
        results[user_index]["slug"] = slug

        # 4. Start BERT training
        schemes = user_api.get_schemes(slug)
        if not schemes:
            raise Exception(f"{tag} No scheme found in project")
        scheme_list = list(schemes) if isinstance(schemes, dict) else schemes
        scheme = scheme_list[0]
        print(f"{tag} Starting BERT training on scheme '{scheme}'...")
        user_api.start_finetune_model(
            project_slug=slug,
            scheme=scheme,
            name=f"stress-model-{user_index}",
            base_model=BASE_MODEL,
        )

        # 5. Verify training started
        try:
            models = wait_for_training(user_api, slug, timeout=60)
            print(f"{tag} Training running: {list(models['training'].keys())}")
            results[user_index]["training_started"] = True
        except TimeoutError:
            print(f"{tag} Warning: training not detected within timeout")

        # Signal ready then wait for stop
        ready_event.set()
        stop_event.wait()

    except Exception as e:
        print(f"{tag} ERROR: {e}")
        results[user_index]["error"] = str(e)
        ready_event.set()  # unblock main even on failure

    finally:
        # Store references for cleanup by main thread
        results[user_index]["user_api"] = user_api


def cleanup(admin_api, results):
    """Tear down all resources created during the benchmark."""
    print("\n--- Cleanup ---")
    for i, res in sorted(results.items()):
        tag = f"[user-{i}]"
        slug = res.get("slug")
        username = res.get("username")
        user_api = res.get("user_api")

        # Stop training if possible
        if slug and user_api and user_api.headers:
            try:
                user_api.stop_finetune_model(slug)
                print(f"{tag} Stopped training")
            except Exception as e:
                print(f"{tag} Warning: could not stop training: {e}")

        # Delete project (user deletes their own)
        if slug and user_api and user_api.headers:
            delete_test_project(user_api, slug)
            print(f"{tag} Deleted project {slug}")

        # Admin deletes the user
        if username:
            delete_test_user(admin_api, username)
            print(f"{tag} Deleted user {username}")


def main():
    parser = argparse.ArgumentParser(description="ActiveTigger stress benchmark")
    parser.add_argument(
        "--users", type=int, default=5, help="Number of concurrent users (default: 5)"
    )
    parser.add_argument(
        "--duration", type=int, default=10, help="Duration in minutes (default: 10)"
    )
    args = parser.parse_args()

    n_users = args.users
    duration_min = args.duration

    print(f"=== Stress Benchmark: {n_users} users, {duration_min} min ===\n")

    admin_api = load_api()
    ping = admin_api.ping()
    check(ping["available"], "API is reachable")
    print(f"  Response time: {ping['response_time_ms']} ms\n")

    # Load data once, shared across all workers
    data = load_test_data()

    results = {i: {} for i in range(n_users)}
    ready_events = [threading.Event() for _ in range(n_users)]
    stop_event = threading.Event()

    # Launch workers
    threads = []
    t_start = time.monotonic()
    for i in range(n_users):
        t = threading.Thread(
            target=worker,
            args=(admin_api, i, data, results, ready_events[i], stop_event),
            daemon=True,
        )
        t.start()
        threads.append(t)

    # Wait for all workers to be ready (or failed)
    for i, evt in enumerate(ready_events):
        evt.wait(timeout=180)
    setup_elapsed = time.monotonic() - t_start

    # Report setup results
    n_ok = sum(1 for r in results.values() if r.get("training_started"))
    n_err = sum(1 for r in results.values() if r.get("error"))
    print(f"\n=== Setup complete in {setup_elapsed:.1f}s ===")
    print(f"  Training started: {n_ok}/{n_users}")
    if n_err:
        print(f"  Errors: {n_err}/{n_users}")

    # Run for the requested duration
    remaining = (duration_min * 60) - (time.monotonic() - t_start)
    if remaining > 0:
        print(f"\nRunning for {remaining:.0f}s (until {duration_min} min elapsed)...")
        try:
            time.sleep(remaining)
        except KeyboardInterrupt:
            print("\nInterrupted by user.")

    # Signal workers to stop and join
    stop_event.set()
    for t in threads:
        t.join(timeout=30)

    # Cleanup
    cleanup(admin_api, results)

    total_elapsed = time.monotonic() - t_start
    print(f"\n=== Benchmark finished in {total_elapsed:.1f}s ===")
    print(f"  Users: {n_users}, Duration: {duration_min} min")
    print(f"  Training started: {n_ok}/{n_users}")
    check(n_ok > 0, "At least one training was started successfully.")


if __name__ == "__main__":
    main()
