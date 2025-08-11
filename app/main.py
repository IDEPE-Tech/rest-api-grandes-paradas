"""Grandes Paradas API main module.

Provides FastAPI application with three endpoints:
    * /hello    : simple health check
    * /optimize : measures number of iterations within a time span
    * /calendar : generates randomized UG maintenance periods
"""

from fastapi import FastAPI
import time
from random import randint, choice
from typing import Any

MAINTENANCE_CODES = [
    'AR', 'CK', 'C', 'CDG', 'CM', 'CM2', 'CV', 'DE', 'ARO', 'RK', 'E',
    'IBK', 'JD', 'RAC', 'R25', 'TRF', 'TAR', 'TK', 'VB', 'VP', 'VPK', 'VE',
]

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
def generate_calendar() -> list[dict[str, Any]]:
    """Generate randomized maintenance periods per generating unit (UG).

    Returns a list of dictionaries; each dictionary aggregates one or more
    continuous maintenance periods for a UG under a given maintenance code.

    Response schema (per item):
        - ``ug``: zero-padded string from "01" to "50"
        - ``maintenance``: string, one of the values defined in ``MAINTENANCE_CODES``
        - ``days``: list[int], days in 1..365 sorted ascending; may contain
          multiple continuous segments if more than one period was generated

    Rules:
        - For each UG, randomly select 1 to 5 maintenance specifications.
        - For each selected specification, generate 1 to 2 independent periods.
        - Each period has a random continuous duration between 20 and 100 days.
        - Periods may overlap (even within the same UG/spec).
    """
    num_units = 50
    num_days_in_year = 365

    activities: list[dict[str, Any]] = []

    for unit_number in range(1, num_units + 1):
        # Randomly choose how many different maintenance codes this UG will have
        num_activities = randint(1, 5)
        for _ in range(num_activities):
            specification = choice(MAINTENANCE_CODES)

            # For this specification, generate 1 to 2 independent periods
            num_periods = randint(1, 2)
            days: list[int] = []
            for _ in range(num_periods):
                duration = randint(20, 100)
                start_day = randint(1, num_days_in_year - duration + 1)
                for day_number in range(start_day, start_day + duration):
                    days.append(day_number)

            days.sort()
            activities.append({
                "ug": f"{unit_number:02d}",
                "maintenance": specification,
                "days": days,
            })

    return activities
