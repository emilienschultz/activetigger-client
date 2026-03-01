"""
Reusable helpers for ActiveTigger API test scripts.

Provides config loading, project/user lifecycle management,
and a simple CLI assertion helper.
"""

import sys
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

import pandas as pd  # type: ignore[import]

from .pyactivetigger import AtApi

# Resolve paths relative to the repo root (parent of atclient/)
_REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = _REPO_ROOT / "tests" / "config.yaml"
DEFAULT_DATA = _REPO_ROOT / "data" / "dataset.parquet"


def load_api(config=None):
    """Create an authenticated AtApi from a config file.

    Args:
        config: Path to a YAML config file. Defaults to tests/config.yaml.

    Returns:
        An authenticated AtApi instance.

    Raises:
        Exception: If the config file is missing or authentication fails.
    """
    config = str(config or DEFAULT_CONFIG)
    api = AtApi(config=config)
    if api.headers is None:
        raise Exception(f"Authentication failed using config {config}")
    return api


def load_test_data(path=None):
    """Load the test dataset as a DataFrame.

    Args:
        path: Path to a parquet file. Defaults to data/dataset.parquet.

    Returns:
        A pandas DataFrame.
    """
    path = Path(path or DEFAULT_DATA)
    return pd.read_parquet(path)


def make_project_name(prefix="test"):
    """Generate a unique project name like 'test-a7f3b2c1'."""
    suffix = uuid.uuid4().hex[:8]
    return f"{prefix}-{suffix}"


def wait_for_project(api, slug, timeout=60, poll_interval=3):
    """Poll until a project is accessible.

    Args:
        api: Authenticated AtApi instance.
        slug: Project slug to wait for.
        timeout: Maximum seconds to wait before raising TimeoutError.
        poll_interval: Seconds between polls.

    Returns:
        The project state dict once available.

    Raises:
        TimeoutError: If the project is not accessible within the timeout.
    """
    deadline = time.monotonic() + timeout
    while True:
        try:
            slugs = api.get_projects_slugs()
            if slug in slugs:
                state = api.get_project_state(slug)
                return state
        except Exception:
            pass  # API may 404 while project is being created

        if time.monotonic() >= deadline:
            raise TimeoutError(
                f"Project '{slug}' not accessible after {timeout}s"
            )
        time.sleep(poll_interval)


def wait_for_training(api, slug, timeout=30, poll_interval=3):
    """Poll until model training is detected.

    Args:
        api: Authenticated AtApi instance.
        slug: Project slug.
        timeout: Maximum seconds to wait before raising TimeoutError.
        poll_interval: Seconds between polls.

    Returns:
        The models dict (with 'available' and 'training' keys).

    Raises:
        TimeoutError: If no training is detected within the timeout.
    """
    deadline = time.monotonic() + timeout
    while True:
        try:
            models = api.get_models(slug)
            if models["training"]:
                return models
        except Exception:
            pass

        if time.monotonic() >= deadline:
            raise TimeoutError(
                f"No model training detected for '{slug}' after {timeout}s"
            )
        time.sleep(poll_interval)


def create_test_project(
    api,
    data=None,
    name=None,
    n_train=1000,
    n_test=100,
    language="fr",
    force_label=False,
    wait=True,
    timeout=60,
):
    """Create a project with sensible test defaults.

    Args:
        api: Authenticated AtApi instance.
        data: DataFrame to upload. Defaults to load_test_data().
        name: Project name. Defaults to make_project_name().
        n_train: Training set size.
        n_test: Test set size.
        language: Project language.
        force_label: Whether to force label assignment from the dataset.
        wait: Whether to poll until the project is ready.
        timeout: Max seconds to wait (if wait=True).

    Returns:
        (slug, state) tuple. state is None if wait=False.
    """
    if data is None:
        data = load_test_data()
    if name is None:
        name = make_project_name()

    slug = api.add_project(
        project_name=name,
        data=data,
        col_id="id",
        cols_text=["text"],
        cols_label=["label"],
        n_train=n_train,
        n_test=n_test,
        language=language,
        force_label=force_label,
    )

    state = None
    if wait:
        state = wait_for_project(api, slug, timeout=timeout)

    return slug, state


def delete_test_project(api, slug):
    """Delete a project, never raises (safe for finally blocks)."""
    try:
        api.delete_project(slug)
    except Exception as e:
        print(f"Warning: failed to delete project '{slug}': {e}")


@contextmanager
def managed_project(api, **kwargs):
    """Context manager that creates a test project and deletes it on exit.

    Usage:
        with managed_project(api, n_train=500) as (slug, state):
            ...

    Accepts the same keyword arguments as create_test_project.
    Cleanup is skipped if project creation fails before returning a slug.
    """
    slug = None
    try:
        slug, state = create_test_project(api, **kwargs)
        yield slug, state
    finally:
        if slug is not None:
            delete_test_project(api, slug)


def create_test_user(api, prefix="testuser", password="Testpass1!", mail=None, status="manager"):
    """Create a user with a generated username.

    Args:
        api: Authenticated AtApi instance.
        prefix: Username prefix.
        password: Password for the new user.
        mail: Contact email. Defaults to <username>@test.local.
        status: User role.

    Returns:
        The generated username.
    """
    username = f"{prefix}-{uuid.uuid4().hex[:8]}"
    if mail is None:
        mail = f"{username}@test.local"
    api.add_user(username=username, password=password, mail=mail, status=status)
    return username


def delete_test_user(api, username):
    """Delete a user, never raises (safe for finally blocks)."""
    try:
        api.delete_user(username)
    except Exception as e:
        print(f"Warning: failed to delete user '{username}': {e}")


@contextmanager
def managed_user(api, **kwargs):
    """Context manager that creates a test user and deletes it on exit.

    Usage:
        with managed_user(api) as username:
            ...

    Accepts the same keyword arguments as create_test_user.
    """
    username = None
    try:
        username = create_test_user(api, **kwargs)
        yield username
    finally:
        if username is not None:
            delete_test_user(api, username)


def check(condition, message):
    """CLI assertion: prints OK/FAIL and exits on failure.

    Args:
        condition: Boolean condition to check.
        message: Description of what is being checked.
    """
    if condition:
        print(f"OK: {message}")
    else:
        print(f"FAIL: {message}")
        sys.exit(1)
