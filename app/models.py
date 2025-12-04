"""Database models for the application."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, ARRAY, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Calendar(Base):
    """Model for calendar metadata."""
    __tablename__ = "calendars"

    id = Column(Integer, primary_key=True, index=True)
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_modified = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    total_activities = Column(Integer, default=0, nullable=False)
    is_active = Column(Integer, default=1, nullable=False)  # 1 for active, 0 for inactive

    # Relationship to activities
    activities = relationship("CalendarActivity", back_populates="calendar", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_calendar_active', 'is_active'),
    )


class CalendarActivity(Base):
    """Model for calendar maintenance activities."""
    __tablename__ = "calendar_activities"

    id = Column(Integer, primary_key=True, index=True)
    calendar_id = Column(Integer, ForeignKey("calendars.id", ondelete="CASCADE"), nullable=False)
    ug = Column(String(10), nullable=False, index=True)
    maintenance = Column(String(10), nullable=False, index=True)
    days = Column(ARRAY(Integer), nullable=False)

    # Relationship to calendar
    calendar = relationship("Calendar", back_populates="activities")

    __table_args__ = (
        Index('idx_activity_ug_maintenance', 'ug', 'maintenance'),
        Index('idx_activity_calendar', 'calendar_id'),
    )

