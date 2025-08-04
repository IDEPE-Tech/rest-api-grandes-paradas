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
    """/calendar must return a 50×365 matrix with one maintenance per day."""
    response = client.get("/calendar")
    assert response.status_code == 200

    payload = response.json()
    assert "calendar" in payload
    matrix = payload["calendar"]

    # Validate dimensions
    assert len(matrix) == 50
    for row in matrix:
        assert len(row) == 365

    # Validate exactly one maintenance per day across GUs
    for day in range(365):
        daily_sum = sum(matrix[gu][day] for gu in range(50))
        assert daily_sum == 1
