from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, Relationship

from app.models.base import BaseModel


class Teacher(BaseModel, table=True):
    """Модель преподавателя"""
    __tablename__ = "teachers"

    name: str = Field(min_length=1, max_length=100)
    email: str = Field(unique=True, min_length=1, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)
    bio: Optional[str] = Field(default=None, max_length=1000)
    is_active: bool = Field(default=True)
    slug: Optional[str] = Field(default=None, max_length=20, unique=True, description="Уникальный username/slug для учителя")

    # Связи
    time_slots: List["TimeSlot"] = Relationship(back_populates="teacher")

if TYPE_CHECKING:
    from app.models.time_slot import TimeSlot
