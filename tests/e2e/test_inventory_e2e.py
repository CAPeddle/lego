"""
End-to-end tests for Inventory API using Playwright.

Tests the complete flow of listing and updating inventory through the REST API.
"""

import pytest
from playwright.sync_api import APIRequestContext


@pytest.mark.e2e
def test_list_inventory_empty(playwright, base_url):
    """Test listing inventory when it's empty."""
    request_context: APIRequestContext = playwright.request.new_context(
        base_url=base_url
    )

    response = request_context.get("/inventory/")

    assert response.ok
    assert response.status == 200
    data = response.json()
    assert "items" in data
    assert "count" in data
    assert isinstance(data["items"], list)
    assert data["count"] == len(data["items"])

    request_context.dispose()


@pytest.mark.e2e
def test_list_inventory_with_state_filter(playwright, base_url):
    """Test listing inventory with state filter."""
    request_context: APIRequestContext = playwright.request.new_context(
        base_url=base_url
    )

    # Test with each valid state
    for state in ["MISSING", "OWNED_LOCKED", "OWNED_FREE"]:
        response = request_context.get(f"/inventory/?state={state}")

        assert response.ok
        assert response.status == 200
        data = response.json()
        assert "items" in data
        assert "count" in data

        # Verify all items have the requested state
        for item in data["items"]:
            assert item["state"] == state

    request_context.dispose()


@pytest.mark.e2e
def test_update_inventory_not_found(playwright, base_url):
    """Test updating an inventory item that doesn't exist."""
    request_context: APIRequestContext = playwright.request.new_context(
        base_url=base_url
    )

    response = request_context.patch(
        "/inventory/",
        data={"part_no": "99999-1", "color_id": 1, "qty": 5, "state": "OWNED_FREE"},
    )

    assert response.status == 404
    data = response.json()
    assert "detail" in data

    request_context.dispose()


@pytest.mark.e2e
def test_update_inventory_validation(playwright, base_url):
    """Test input validation for updating inventory."""
    request_context: APIRequestContext = playwright.request.new_context(
        base_url=base_url
    )

    # Test with invalid part_no format
    response = request_context.patch(
        "/inventory/",
        data={
            "part_no": "a",  # Too short
            "color_id": 1,
            "qty": 5,
            "state": "OWNED_FREE",
        },
    )
    assert response.status == 422

    # Test with invalid color_id (negative)
    response = request_context.patch(
        "/inventory/",
        data={"part_no": "3001", "color_id": -1, "qty": 5, "state": "OWNED_FREE"},
    )
    assert response.status == 422

    # Test with invalid qty (zero)
    response = request_context.patch(
        "/inventory/",
        data={"part_no": "3001", "color_id": 1, "qty": 0, "state": "OWNED_FREE"},
    )
    assert response.status == 422

    # Test with invalid qty (too large)
    response = request_context.patch(
        "/inventory/",
        data={"part_no": "3001", "color_id": 1, "qty": 99999, "state": "OWNED_FREE"},
    )
    assert response.status == 422

    # Test with invalid state
    response = request_context.patch(
        "/inventory/",
        data={"part_no": "3001", "color_id": 1, "qty": 5, "state": "INVALID_STATE"},
    )
    assert response.status == 422

    request_context.dispose()


@pytest.mark.e2e
def test_inventory_workflow(playwright, base_url):
    """
    Test a complete inventory workflow.

    This test demonstrates the flow but will fail without actual data.
    In a real scenario, you'd set up test data first.
    """
    request_context: APIRequestContext = playwright.request.new_context(
        base_url=base_url
    )

    # 1. Check initial inventory
    response = request_context.get("/inventory/")
    assert response.ok
    initial_data = response.json()

    # 2. If we had a way to add test inventory items, we would do that here
    # For now, we just verify the API structure is correct
    assert "items" in initial_data
    assert "count" in initial_data
    assert isinstance(initial_data["items"], list)

    # 3. Filter by state
    response = request_context.get("/inventory/?state=OWNED_FREE")
    assert response.ok
    filtered_data = response.json()
    assert all(item["state"] == "OWNED_FREE" for item in filtered_data["items"])

    request_context.dispose()
