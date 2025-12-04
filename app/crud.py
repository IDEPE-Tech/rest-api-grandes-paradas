"""CRUD operations for calendar database operations."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified
from typing import List, Optional
from datetime import datetime
from models import Calendar, CalendarActivity, Optimizer
from schemas import CalendarActivityResponse


async def get_active_calendar(db: AsyncSession) -> Optional[Calendar]:
    """Get the active calendar with all activities."""
    result = await db.execute(
        select(Calendar)
        .where(Calendar.is_active == 1)
        .options(selectinload(Calendar.activities))
        .order_by(Calendar.generated_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def deactivate_all_calendars(db: AsyncSession) -> None:
    """Deactivate all existing calendars."""
    await db.execute(
        update(Calendar)
        .where(Calendar.is_active == 1)
        .values(is_active=0)
    )


async def create_calendar(
    db: AsyncSession,
    activities: List[dict]
) -> Calendar:
    """Create a new calendar and deactivate old ones."""
    # Deactivate all existing calendars
    await deactivate_all_calendars(db)

    # Create new calendar
    calendar = Calendar(
        generated_at=datetime.now(),
        last_modified=datetime.now(),
        total_activities=len(activities),
        is_active=1
    )
    db.add(calendar)
    await db.flush()  # Get the calendar ID

    # Create activities
    for activity_data in activities:
        activity = CalendarActivity(
            calendar_id=calendar.id,
            ug=activity_data["ug"],
            maintenance=activity_data["maintenance"],
            days=activity_data["days"]
        )
        db.add(activity)

    await db.flush()
    await db.refresh(calendar)
    return calendar


async def get_calendar_activities(db: AsyncSession) -> List[CalendarActivityResponse]:
    """Get all activities from the active calendar."""
    calendar = await get_active_calendar(db)
    if not calendar:
        print("DEBUG: No active calendar found")
        return []

    if not calendar.activities:
        print(f"DEBUG: Calendar {calendar.id} found but has no activities")
        return []

    print(f"DEBUG: Found calendar {calendar.id} with {len(calendar.activities)} activities")
    # Sort activities: first by UG (numeric), then by maintenance (alphabetical)
    sorted_activities = sorted(
        calendar.activities,
        key=lambda act: (int(act.ug), act.maintenance)
    )
    return [
        CalendarActivityResponse(
            ug=activity.ug,
            maintenance=activity.maintenance,
            days=activity.days
        )
        for activity in sorted_activities
    ]


async def update_activity_days(
    db: AsyncSession,
    ug: str,
    maintenance: str,
    old_days: List[int],
    new_days: List[int]
) -> bool:
    """Update days for a specific activity."""
    calendar = await get_active_calendar(db)
    if not calendar:
        return False

    # Find the activity
    activity = None
    for act in calendar.activities:
        if act.ug == ug and act.maintenance == maintenance:
            activity = act
            break

    if not activity:
        return False

    # Verify old days match
    current_days_set = set(activity.days)
    old_days_set = set(old_days)

    if not old_days_set.issubset(current_days_set):
        return False

    # Update days
    new_days_list = [day for day in activity.days if day not in old_days_set]
    new_days_list.extend(new_days)
    activity.days = sorted(list(set(new_days_list)))
    
    # Flag the array as modified so SQLAlchemy detects the change
    flag_modified(activity, "days")

    # Update calendar last_modified
    calendar.last_modified = datetime.now()

    # Flush changes to database
    await db.flush()
    # Refresh to ensure changes are visible in the session
    await db.refresh(activity)
    await db.refresh(calendar)
    # Explicitly commit to ensure changes are persisted
    await db.commit()
    return True


# ---------- Optimizer CRUD Operations ----------


async def get_active_optimizer(db: AsyncSession) -> Optimizer:
    """Get the active optimizer configuration. Creates default if none exists."""
    result = await db.execute(
        select(Optimizer)
        .where(Optimizer.is_active == 1)
        .order_by(Optimizer.created_at.desc())
        .limit(1)
    )
    optimizer = result.scalar_one_or_none()
    
    # If no active optimizer exists, create one with default values
    if optimizer is None:
        optimizer = Optimizer(
            method="AG",
            mode="time",
            n_pop=50,
            n_gen=None,
            n_ants=30,
            n_iter=None,
            time=60,
            is_active=1
        )
        db.add(optimizer)
        await db.flush()
        await db.refresh(optimizer)
    
    return optimizer


async def deactivate_all_optimizers(db: AsyncSession) -> None:
    """Deactivate all existing optimizer configurations."""
    await db.execute(
        update(Optimizer)
        .where(Optimizer.is_active == 1)
        .values(is_active=0)
    )


async def create_or_update_optimizer(
    db: AsyncSession,
    method: str,
    mode: str,
    n_pop: Optional[int] = None,
    n_gen: Optional[int] = None,
    n_ants: Optional[int] = None,
    n_iter: Optional[int] = None,
    time: Optional[int] = None
) -> Optimizer:
    """Create or update optimizer parameters configuration."""
    # Deactivate all existing optimizers
    await deactivate_all_optimizers(db)
    
    # Create new optimizer configuration
    optimizer = Optimizer(
        method=method,
        mode=mode,
        n_pop=n_pop,
        n_gen=n_gen,
        n_ants=n_ants,
        n_iter=n_iter,
        time=time,
        is_active=1
    )
    db.add(optimizer)
    await db.flush()
    await db.refresh(optimizer)
    return optimizer

