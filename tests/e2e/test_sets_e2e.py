"""
End-to-end tests for LEGO Sets API using Playwright.

Tests the complete flow of adding LEGO sets through the REST API.
"""

import pytest
from playwright.sync_api import APIRequestContext


@pytest.mark.e2e
def test_health_check(playwright, base_url):
    """Test that the health endpoint is accessible."""
    request_context: APIRequestContext = playwright.request.new_context(
        base_url=base_url
    )

    response = request_context.get("/health")

    assert response.ok
    assert response.status == 200
    data = response.json()
    # Health check should return a status field (ok or error)
    assert "status" in data
    assert data["status"] in ["ok", "error"]

    request_context.dispose()


@pytest.mark.e2e
def test_add_set_response_structure(playwright, base_url):
    """
    Test adding a LEGO set through the API response structure.

    Note: This test verifies the API handles set addition requests properly,
    regardless of whether the set exists in Bricklink.
    """
    request_context: APIRequestContext = playwright.request.new_context(
        base_url=base_url
    )

    # Test with a set number
    response = request_context.post(
        "/sets/", data={"set_no": "75192-1", "assembled": False}
    )

    # The API should return a valid response (success or error)
    assert response.status in [
        200,
        404,
        502,
    ], f"Got unexpected status {response.status}"

    # If successful, verify response structure
    if response.status == 200:
        data = response.json()
        assert "ok" in data
        assert "set" in data

    request_context.dispose()


@pytest.mark.e2e
def test_add_set_validation(playwright, base_url):
    """Test input validation for adding a set."""
    request_context: APIRequestContext = playwright.request.new_context(
        base_url=base_url
    )

    # Test with invalid set_no format (too short)
    response = request_context.post("/sets/", data={"set_no": "ab", "assembled": False})

    assert response.status == 422  # Validation error

    # Test with invalid set_no format (special characters)
    response = request_context.post(
        "/sets/", data={"set_no": "invalid@set!", "assembled": False}
    )

    assert response.status == 422  # Validation error

    request_context.dispose()


@pytest.mark.e2e
def test_add_set_missing_fields(playwright, base_url):
    """Test that required fields are enforced."""
    request_context: APIRequestContext = playwright.request.new_context(
        base_url=base_url
    )

    # Test with missing set_no
    response = request_context.post("/sets/", data={"assembled": False})

    assert response.status == 422  # Validation error

    request_context.dispose()
