from datetime import datetime
from typing import Optional
from enum import Enum

from sqlmodel import Field, Relationship

from app.models.base import BaseModel


class BookingStatus(str, Enum):
    """Статусы бронирования"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Booking(BaseModel, table=True):
    """Модель бронирования"""
    __tablename__ = "bookings"

    time_slot_id: int = Field(foreign_key="time_slots.id")
    student_id: int = Field(foreign_key="students.id")
    status: BookingStatus = Field(default=BookingStatus.PENDING)
    student_notes: Optional[str] = Field(default=None, max_length=500)
    teacher_notes: Optional[str] = Field(default=None, max_length=500)
    booking_time: datetime = Field(index=True)
    confirmed_at: Optional[datetime] = Field(default=None)
    cancelled_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)

    # Связи
    time_slot: "TimeSlot" = Relationship(back_populates="bookings")
    student: "Student" = Relationship(back_populates="bookings")
