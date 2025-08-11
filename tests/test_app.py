"""Basic integration tests for the Grandes Paradas API.

Run with:
    pytest -q
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_hello() -> None:
    """/hello should return HTTP 200 and the expected greeting."""
    response = client.get("/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "hello"}


def test_optimize() -> None:
    """/optimize should accept a query parameter *n* and respond with stats.

    We use n=1 to keep the test reasonably fast. The elapsed time should be at
    least 1 s but not wildly greater (allow generous upper bound to avoid flaky
    CI on slow machines).
    """
    response = client.post("/optimize", params={"n": 1})
    assert response.status_code == 200

    data = response.json()
    assert "n" in data and "elapsed_seconds" in data
    assert isinstance(data["n"], int)
    assert isinstance(data["elapsed_seconds"], (int, float))
    # elapsed_seconds should be roughly >= 1
    assert data["elapsed_seconds"] >= 1


def test_calendar_structure() -> None:
    """/calendar must return a list of dicts with expected keys and value types."""
    response = client.get("/calendar")
    assert response.status_code == 200

    payload = response.json()
    # Non-empty list
    assert isinstance(payload, list)
    assert len(payload) > 0

    # Validate structure of a sample
    sample = payload[:10]
    for item in sample:
        assert set(item.keys()) == {"ug", "maintenance", "days"}
        assert isinstance(item["ug"], str) and len(item["ug"]) == 2 and item["ug"].isdigit()
        assert 1 <= int(item["ug"]) <= 50
        assert isinstance(item["maintenance"], str)
        assert isinstance(item["days"], list) and len(item["days"]) >= 1
        # Days must be within 1..365 and sorted ascending
        days = item["days"]
        assert all(isinstance(d, int) and 1 <= d <= 365 for d in days)
        assert days == sorted(days)
