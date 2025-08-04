"""Grandes Paradas API main module.

Provides FastAPI application with three endpoints:
    * /hello    : simple health check
    * /optimize : measures number of iterations within a time span
    * /calendar : generates a maintenance calendar matrix
"""

from fastapi import FastAPI
import time
from random import randint

app = FastAPI(title="Grandes Paradas API")


@app.get("/hello")
async def hello() -> dict[str, str]:
    """Return a simple greeting.

    Acts as a health-check endpoint for the API.
    """
    return {"message": "hello"}


# ---------- Optimize Endpoint ----------


@app.post("/optimize")
def optimize(n: int) -> dict[str, float | int]:
    """Busy-loop for *n* seconds and return executed iterations.

    Parameters
    ----------
    n : int
        Target duration in seconds for which the busy loop should run.

    Returns
    -------
    dict
        Dictionary with:
            • ``n``: number of iterations performed
            • ``elapsed_seconds``: actual elapsed time in seconds
    """
    start = time.perf_counter()
    counter = 0

    while time.perf_counter() - start < n:
        counter += 1

    elapsed = time.perf_counter() - start
    return {"n": counter, "elapsed_seconds": elapsed}


# ---------- Calendar Endpoint ----------


@app.get("/calendar")
def generate_calendar() -> dict[str, list[list[int]]]:
    """Generate a 50×365 matrix indicating planned maintenance.

    Returns
    -------
    dict
        Dictionary containing the maintenance calendar matrix under
        the key ``calendar``.
    """
    total_gus = 50
    total_days = 365

    # Pre-populate the matrix with zeroes
    matrix = [[0 for _ in range(total_days)] for _ in range(total_gus)]

    day = 0
    while day < total_days:
        gu = randint(0, total_gus - 1)
        duration = randint(1, 10)

        # Ensure we do not overshoot the end of the year
        duration = min(duration, total_days - day)

        # Flag maintenance days
        for d in range(day, day + duration):
            matrix[gu][d] = 1

        day += duration

    return {"calendar": matrix}
