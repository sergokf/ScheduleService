from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.models.booking import BookingStatus
from app.schemas.base import BaseResponse


class BookingBase(BaseModel):
    """Базовая схема бронирования"""
    time_slot_id: int = Field(gt=0)
    student_id: int = Field(gt=0)
    student_notes: Optional[str] = Field(default=None, max_length=500)


class BookingCreate(BookingBase):
    """Схема создания бронирования"""
    pass


class BookingUpdate(BaseModel):
    """Схема обновления бронирования"""
    status: Optional[BookingStatus] = None
    student_notes: Optional[str] = Field(None, max_length=500)
    teacher_notes: Optional[str] = Field(None, max_length=500)


class BookingResponse(BaseResponse):
    """Схема ответа бронирования"""
    time_slot_id: int
    student_id: int
    status: BookingStatus
    student_notes: Optional[str]
    teacher_notes: Optional[str]
    booking_time: datetime
    confirmed_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class BookingWithDetails(BookingResponse):
    """Схема бронирования с деталями"""
    time_slot: "TimeSlotResponse"
    student: "StudentResponse"

    class Config:
        from_attributes = True


class BookingConfirm(BaseModel):
    """Схема подтверждения бронирования"""
    teacher_notes: Optional[str] = Field(None, max_length=500)


class BookingCancel(BaseModel):
    """Схема отмены бронирования"""
    reason: Optional[str] = Field(None, max_length=500)


# Импорты будут добавлены в конце файла
from app.schemas.time_slot import TimeSlotResponse
from app.schemas.student import StudentResponse
BookingWithDetails.model_rebuild()
