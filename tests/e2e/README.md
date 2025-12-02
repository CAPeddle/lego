# End-to-End Tests with Playwright

This directory contains end-to-end tests for the LEGO Inventory Service using Playwright.

## Overview

These tests verify the complete functionality of the API by:
- Starting a real FastAPI server
- Making HTTP requests through Playwright's API context
- Testing actual response structures and behavior

## Test Coverage

### Sets API (`test_sets_e2e.py`)
- ✅ Health check endpoint accessibility
- ✅ Set addition response structure validation
- ✅ Input validation (invalid format, missing fields)
- ✅ Error handling for malformed requests

### Inventory API (`test_inventory_e2e.py`)
- ✅ List inventory (empty and populated)
- ✅ State filtering (MISSING, OWNED_LOCKED, OWNED_FREE)
- ✅ Update inventory item validation
- ✅ Complete inventory workflow
- ✅ Error handling (not found, invalid input)

## Running E2E Tests

### Run E2E tests only:
```bash
pytest tests/e2e/ -v -m e2e
```

### Run without E2E tests:
```bash
pytest -m "not e2e"
```

### Run all unit tests (excluding E2E):
```bash
pytest tests/ -m "not e2e" -v
```

## Important Notes

⚠️ **Event Loop Conflict**: Due to event loop management differences between `pytest-asyncio` and `pytest-playwright`, run E2E tests separately from unit tests. This is actually a best practice as E2E tests are typically slower and test different concerns.

✅ **Isolation**: Each E2E test runs against a fresh test database in a temporary directory, ensuring complete test isolation.

✅ **Real Server**: Tests start an actual uvicorn server on port 8082, making these true end-to-end tests.

## Test Structure

```
tests/e2e/
├── README.md              # This file
├── __init__.py            # Package marker
├── conftest.py            # Pytest fixtures (server setup, test DB)
├── test_sets_e2e.py       # Sets API E2E tests
└── test_inventory_e2e.py  # Inventory API E2E tests
```

## Fixtures

### `base_url` (session scope)
Starts a FastAPI server on port 8082 with a test database and returns the base URL. Server is automatically cleaned up after tests complete.

### `test_db_path` (session scope)
Creates a temporary database file for E2E tests, cleaned up after tests complete.

### `playwright_config`
Provides Playwright configuration (base URL, browser type, headless mode).

## Adding New Tests

1. Create a new test file in `tests/e2e/` following the pattern `test_<feature>_e2e.py`
2. Mark tests with `@pytest.mark.e2e` decorator
3. Use the `playwright` fixture to create request contexts
4. Use the `base_url` fixture to get the server URL

Example:
```python
import pytest
from playwright.sync_api import APIRequestContext

@pytest.mark.e2e
def test_my_feature(playwright, base_url):
    request_context: APIRequestContext = playwright.request.new_context(
        base_url=base_url
    )

    response = request_context.get("/my-endpoint")
    assert response.ok

    request_context.dispose()
```

## Troubleshooting

### Server won't start
- Check if port 8082 is already in use
- Verify virtual environment is activated
- Check that all dependencies are installed

### Tests hang or timeout
- Increase timeout in `conftest.py` `base_url` fixture
- Check server logs for startup errors
- Verify database can be created in temp directory

### Browser installation errors
If Playwright browsers aren't installed:
```bash
python -m playwright install chromium
```
