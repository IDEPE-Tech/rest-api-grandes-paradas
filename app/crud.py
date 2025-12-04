"""CRUD operations for calendar database operations."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified
from typing import List, Optional
from datetime import datetime
from models import (
    Calendar, 
    CalendarActivity, 
    Optimizer,
    DEFAULT_OPTIMIZER_METHOD,
    DEFAULT_OPTIMIZER_MODE,
    DEFAULT_OPTIMIZER_N_POP,
    DEFAULT_OPTIMIZER_N_GEN,
    DEFAULT_OPTIMIZER_N_ANTS,
    DEFAULT_OPTIMIZER_N_ITER,
    DEFAULT_OPTIMIZER_TIME
)
from schemas import CalendarActivityResponse

# Default user identifier
DEFAULT_USER = "default"


async def get_active_calendar(db: AsyncSession, user: str) -> Optional[Calendar]:
    """Get the active calendar with all activities for a specific user."""
    result = await db.execute(
        select(Calendar)
        .where(Calendar.user == user)
        .where(Calendar.is_active == 1)
        .options(selectinload(Calendar.activities))
        .order_by(Calendar.generated_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def deactivate_all_calendars(db: AsyncSession, user: str) -> None:
    """Deactivate all existing calendars for a specific user."""
    await db.execute(
        update(Calendar)
        .where(Calendar.user == user)
        .where(Calendar.is_active == 1)
        .values(is_active=0)
    )


async def create_calendar(
    db: AsyncSession,
    activities: List[dict],
    user: str
) -> Calendar:
    """Create a new calendar and deactivate old ones for a specific user."""
    # Deactivate all existing calendars for this user
    await deactivate_all_calendars(db, user)

    # Create new calendar
    calendar = Calendar(
        user=user,
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


async def get_calendar_activities(db: AsyncSession, user: str) -> List[CalendarActivityResponse]:
    """Get all activities from the active calendar for a specific user. Returns default user's calendar if user doesn't have one."""
    calendar = await get_active_calendar(db, user)
    if not calendar:
        # If user doesn't have a calendar, try default user's calendar
        calendar = await get_active_calendar(db, DEFAULT_USER)
        if not calendar:
            print(f"DEBUG: No active calendar found for user {user} or default user")
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
    user: str,
    ug: str,
    maintenance: str,
    old_days: List[int],
    new_days: List[int]
) -> bool:
    """Update days for a specific activity for a specific user."""
    calendar = await get_active_calendar(db, user)
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


async def get_active_optimizer(db: AsyncSession, user: str) -> Optimizer:
    """Get the active optimizer configuration for a specific user. Returns default user's config if user doesn't have one."""
    result = await db.execute(
        select(Optimizer)
        .where(Optimizer.user == user)
        .where(Optimizer.is_active == 1)
        .order_by(Optimizer.created_at.desc())
        .limit(1)
    )
    optimizer = result.scalar_one_or_none()
    
    # If user doesn't have an optimizer, return default user's optimizer
    if optimizer is None:
        default_result = await db.execute(
            select(Optimizer)
            .where(Optimizer.user == DEFAULT_USER)
            .where(Optimizer.is_active == 1)
            .order_by(Optimizer.created_at.desc())
            .limit(1)
        )
        optimizer = default_result.scalar_one_or_none()
        
        # If default user doesn't exist either, create it
        if optimizer is None:
            await initialize_default_user_data(db)
            # Try again to get default optimizer
            default_result = await db.execute(
                select(Optimizer)
                .where(Optimizer.user == DEFAULT_USER)
                .where(Optimizer.is_active == 1)
                .order_by(Optimizer.created_at.desc())
                .limit(1)
            )
            optimizer = default_result.scalar_one_or_none()
    
    return optimizer


async def deactivate_all_optimizers(db: AsyncSession, user: str) -> None:
    """Deactivate all existing optimizer configurations for a specific user."""
    await db.execute(
        update(Optimizer)
        .where(Optimizer.user == user)
        .where(Optimizer.is_active == 1)
        .values(is_active=0)
    )


async def create_or_update_optimizer(
    db: AsyncSession,
    user: str,
    method: str,
    mode: str,
    n_pop: Optional[int] = None,
    n_gen: Optional[int] = None,
    n_ants: Optional[int] = None,
    n_iter: Optional[int] = None,
    time: Optional[int] = None
) -> Optimizer:
    """Create or update optimizer parameters configuration for a specific user."""
    # Deactivate all existing optimizers for this user
    await deactivate_all_optimizers(db, user)
    
    # Create new optimizer configuration
    optimizer = Optimizer(
        user=user,
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


# ---------- User Initialization Functions ----------


async def initialize_default_user_data(db: AsyncSession) -> None:
    """Initialize default user data if it doesn't exist."""
    # Check if default user optimizer exists
    result = await db.execute(
        select(Optimizer)
        .where(Optimizer.user == DEFAULT_USER)
        .limit(1)
    )
    default_optimizer = result.scalar_one_or_none()
    
    if not default_optimizer:
        # Create default optimizer using model defaults
        optimizer = Optimizer(
            user=DEFAULT_USER,
            method=DEFAULT_OPTIMIZER_METHOD,
            mode=DEFAULT_OPTIMIZER_MODE,
            n_pop=DEFAULT_OPTIMIZER_N_POP,
            n_gen=DEFAULT_OPTIMIZER_N_GEN,
            n_ants=DEFAULT_OPTIMIZER_N_ANTS,
            n_iter=DEFAULT_OPTIMIZER_N_ITER,
            time=DEFAULT_OPTIMIZER_TIME,
            is_active=1
        )
        db.add(optimizer)
        await db.flush()


async def ensure_user_has_data(db: AsyncSession, user: str) -> None:
    """Ensure a user has data by copying from default user if needed."""
    if user == DEFAULT_USER:
        await initialize_default_user_data(db)
        return
    
    # Check if user has an optimizer
    result = await db.execute(
        select(Optimizer)
        .where(Optimizer.user == user)
        .limit(1)
    )
    user_optimizer = result.scalar_one_or_none()
    
    if not user_optimizer:
        # Copy optimizer from default user
        default_result = await db.execute(
            select(Optimizer)
            .where(Optimizer.user == DEFAULT_USER)
            .where(Optimizer.is_active == 1)
            .order_by(Optimizer.created_at.desc())
            .limit(1)
        )
        default_optimizer = default_result.scalar_one_or_none()
        
        if default_optimizer:
            # Create copy for new user
            new_optimizer = Optimizer(
                user=user,
                method=default_optimizer.method,
                mode=default_optimizer.mode,
                n_pop=default_optimizer.n_pop,
                n_gen=default_optimizer.n_gen,
                n_ants=default_optimizer.n_ants,
                n_iter=default_optimizer.n_iter,
                time=default_optimizer.time,
                is_active=1
            )
            db.add(new_optimizer)
            await db.flush()
    
    # Check if user has a calendar
    user_calendar = await get_active_calendar(db, user)
    if not user_calendar:
        # Copy calendar from default user
        default_calendar = await get_active_calendar(db, DEFAULT_USER)
        if default_calendar:
            # Create copy for new user
            new_calendar = Calendar(
                user=user,
                generated_at=datetime.now(),
                last_modified=datetime.now(),
                total_activities=default_calendar.total_activities,
                is_active=1
            )
            db.add(new_calendar)
            await db.flush()
            
            # Copy activities
            for activity in default_calendar.activities:
                new_activity = CalendarActivity(
                    calendar_id=new_calendar.id,
                    ug=activity.ug,
                    maintenance=activity.maintenance,
                    days=activity.days.copy()
                )
                db.add(new_activity)
            await db.flush()

