from datetime import datetime, timezone
from typing import Optional, List, Annotated
from pydantic import BaseModel, Field, validator, conlist

from app.models.time_slot import SlotStatus
from app.schemas.base import BaseResponse


class TimeSlotBase(BaseModel):
    """Базовая схема временного слота"""
    teacher_id: int = Field(gt=0)
    start_time: datetime
    end_time: datetime
    max_students: int = Field(default=1, ge=1, le=10)
    description: Optional[str] = Field(default=None, max_length=500)
    price: Optional[float] = Field(default=None, ge=0)

    @validator('end_time')
    def validate_end_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v

    @validator('start_time')
    def validate_start_time(cls, v):
        now = datetime.now(timezone.utc)
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        if v < now:
            raise ValueError('Start time cannot be in the past')
        return v


class TimeSlotCreate(TimeSlotBase):
    """Схема создания временного слота"""
    pass


class TimeSlotUpdate(BaseModel):
    """Схема обновления временного слота"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    max_students: Optional[int] = Field(None, ge=1, le=10)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[float] = Field(None, ge=0)
    status: Optional[SlotStatus] = None

    @validator('end_time')
    def validate_end_time(cls, v, values):
        if v and 'start_time' in values and values['start_time'] and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v


class TimeSlotResponse(BaseResponse):
    """Схема ответа временного слота"""
    teacher_id: int
    start_time: datetime
    end_time: datetime
    max_students: int
    current_bookings: int
    status: SlotStatus
    description: Optional[str]
    price: Optional[float]
    is_available: bool
    is_full: bool

    class Config:
        from_attributes = True


class TimeSlotWithDetails(TimeSlotResponse):
    """Схема временного слота с деталями"""
    teacher: "TeacherResponse"
    bookings: List["BookingResponse"] = []

    class Config:
        from_attributes = True


class BulkSlotCreate(BaseModel):
    """Схема для массового создания слотов"""
    teacher_id: int = Field(gt=0)
    start_date: datetime
    end_date: datetime
    start_time: str = Field(pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    end_time: str = Field(pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    days_of_week: Annotated[list[int], conlist(int, min_length=1, max_length=7)]  # 0-6, где 0 - понедельник
    max_students: int = Field(default=1, ge=1, le=10)
    description: Optional[str] = Field(default=None, max_length=500)
    price: Optional[float] = Field(default=None, ge=0)

    @validator('days_of_week')
    def validate_days_of_week(cls, v):
        if not all(0 <= day <= 6 for day in v):
            raise ValueError('Days of week must be between 0 and 6')
        return v


# Импорты будут добавлены в конце файла
from app.schemas.teacher import TeacherResponse
from app.schemas.booking import BookingResponse
TimeSlotWithDetails.model_rebuild()
