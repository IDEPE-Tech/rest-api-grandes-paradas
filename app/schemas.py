"""Pydantic schemas for request/response validation."""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class EditMaintenanceRequest(BaseModel):
    """Model for editing maintenance days."""
    ug: str
    maintenance: str
    old_days: List[int]
    new_days: List[int]


class CalendarActivityResponse(BaseModel):
    """Response model for calendar activity."""
    ug: str
    maintenance: str
    days: List[int]

    class Config:
        from_attributes = True


class CalendarResponse(BaseModel):
    """Response model for calendar metadata."""
    id: int
    generated_at: datetime
    last_modified: datetime
    total_activities: int

    class Config:
        from_attributes = True

