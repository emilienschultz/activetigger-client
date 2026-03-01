"""
Test if the client can create a user, grant project access, and clean up.
Usage: python test_api_create_users.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from atclient.automate import load_api, managed_project, managed_user, check


def main():
    api = load_api()

    print("Creating test project and user...")
    with managed_project(api) as (slug, state):
        with managed_user(api) as username:
            print(f"  Project slug: {slug}")
            print(f"  Username: {username}")

            # Verify user appears in user list
            users = api.get_users()
            check(username in users, "User found in user list.")

            # Grant user access to the project
            api.add_auth_user_project(username, slug)
            print(f"  Granted '{username}' access to '{slug}'.")

            # Revoke user access
            api.delete_auth_user_project(username, slug)
            print(f"  Revoked '{username}' access from '{slug}'.")

            check(True, "User creation and project auth lifecycle successful.")


if __name__ == "__main__":
    main()
