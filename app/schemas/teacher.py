from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator
import re

from app.schemas.base import BaseResponse


class TeacherBase(BaseModel):
    """Базовая схема преподавателя"""
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=20)
    bio: Optional[str] = Field(default=None, max_length=1000)
    is_active: bool = True
    slug: str = Field(..., min_length=3, max_length=20, pattern=r'^[a-zA-Z0-9_-]+$', description="Уникальный username/slug для учителя")

    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]{3,20}$', v):
            raise ValueError('Slug должен содержать только латинские буквы, цифры, -, _ и быть длиной 3-20 символов')
        return v


class TeacherCreate(TeacherBase):
    """Схема создания преподавателя"""
    pass


class TeacherUpdate(BaseModel):
    """Схема обновления преподавателя"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    bio: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None
    slug: Optional[str] = Field(None, min_length=3, max_length=20, pattern=r'^[a-zA-Z0-9_-]+$', description="Уникальный username/slug для учителя")

    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v):
        if v is not None and not re.match(r'^[a-zA-Z0-9_-]{3,20}$', v):
            raise ValueError('Slug должен содержать только латинские буквы, цифры, -, _ и быть длиной 3-20 символов')
        return v


class TeacherResponse(BaseResponse):
    """Схема ответа преподавателя"""
    name: str
    email: str
    phone: Optional[str]
    bio: Optional[str]
    is_active: bool
    slug: str

    class Config:
        from_attributes = True


class TeacherWithSlots(TeacherResponse):
    """Схема преподавателя со слотами"""
    time_slots: List["TimeSlotResponse"] = []

    class Config:
        from_attributes = True


# Импорт нужно будет добавить в конец файла после определения всех схем
from app.schemas.time_slot import TimeSlotResponse
TeacherWithSlots.model_rebuild()
