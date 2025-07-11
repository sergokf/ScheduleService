from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel

from app.models.base import BaseModel


class SlotStatus(str, Enum):
    """Статусы временного слота"""
    AVAILABLE = "available"
    BOOKED = "booked"
    CANCELLED = "cancelled"


class TimeSlot(BaseModel, table=True):
    """Модель временного слота"""
    __tablename__ = "time_slots"

    teacher_id: int = Field(foreign_key="teachers.id")
    start_time: datetime = Field(index=True)
    end_time: datetime = Field(index=True)
    max_students: int = Field(default=1, ge=1, le=10)
    current_bookings: int = Field(default=0, ge=0)
    status: SlotStatus = Field(default=SlotStatus.AVAILABLE)
    description: Optional[str] = Field(default=None, max_length=500)
    price: Optional[float] = Field(default=None, ge=0)
    meeting_url: Optional[str] = Field(default=None, max_length=500)  # ссылка на встречу

    # Связи
    teacher: "Teacher" = Relationship(back_populates="time_slots")
    bookings: List["Booking"] = Relationship(back_populates="time_slot")

    @property
    def is_available(self) -> bool:
        """Проверка доступности слота"""
        return (
            self.status == SlotStatus.AVAILABLE and
            self.current_bookings < self.max_students and
            not self.is_deleted
        )

    @property
    def is_full(self) -> bool:
        """Проверка заполненности слота"""
        return self.current_bookings >= self.max_students

if TYPE_CHECKING:
    from app.models.teacher import Teacher
    from app.models.booking import Booking
