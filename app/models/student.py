from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, Relationship

from app.models.base import BaseModel


class Student(BaseModel, table=True):
    """Модель студента"""
    __tablename__ = "students"

    name: str = Field(min_length=1, max_length=100)
    email: str = Field(unique=True, min_length=1, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)
    is_active: bool = Field(default=True)
    slug: Optional[str] = Field(default=None, max_length=20, unique=True, description="Уникальный username/slug для студента")
    password_hash: Optional[str] = Field(default=None, max_length=128, description="Хеш пароля студента")

    # Связи
    bookings: List["Booking"] = Relationship(back_populates="student")

if TYPE_CHECKING:
    from app.models.booking import Booking
