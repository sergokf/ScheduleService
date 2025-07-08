from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

from app.schemas.base import BaseResponse


class StudentBase(BaseModel):
    """Базовая схема студента"""
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=20)
    is_active: bool = True


class StudentCreate(StudentBase):
    """Схема создания студента"""
    pass


class StudentUpdate(BaseModel):
    """Схема обновления студента"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None


class StudentResponse(BaseResponse):
    """Схема ответа студента"""
    name: str
    email: str
    phone: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


class StudentWithBookings(StudentResponse):
    """Схема студента с бронированиями"""
    bookings: List["BookingResponse"] = []

    class Config:
        from_attributes = True


# Импорт нужно будет добавить в конец файла после определения всех схем
from app.schemas.booking import BookingResponse
StudentWithBookings.model_rebuild()
