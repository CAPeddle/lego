"""
Pytest fixtures for E2E tests with Playwright.

This module provides fixtures for running the FastAPI application
in a test server and connecting to it with Playwright.
"""

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def test_db_path():
    """Create a temporary database for E2E tests."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_lego_e2e.db"
    yield str(db_path)
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def base_url(test_db_path):
    """
    Start the FastAPI server for E2E tests.

    Returns the base URL of the running server.
    """
    # Set test database path
    env = os.environ.copy()
    env["LEGO_DB_PATH"] = test_db_path
    env["LEGO_LOG_LEVEL"] = "WARNING"  # Reduce log noise

    # Start uvicorn server in background
    port = 8082  # Use different port than dev server
    process = subprocess.Popen(
        [
            "venv/Scripts/python.exe",
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to start
    base_url = f"http://127.0.0.1:{port}"
    max_retries = 30
    for i in range(max_retries):
        try:
            import requests

            response = requests.get(f"{base_url}/health", timeout=1)
            if response.status_code == 200:
                break
        except Exception:
            time.sleep(0.5)
    else:
        process.kill()
        raise RuntimeError("Server failed to start within timeout")

    yield base_url

    # Cleanup: kill server
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


@pytest.fixture
def playwright_config(base_url):
    """Configure Playwright for E2E tests."""
    return {
        "base_url": base_url,
        "browser_type": "chromium",
        "headless": True,
    }
