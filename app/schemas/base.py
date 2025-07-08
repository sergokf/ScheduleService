from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """Базовая схема ответа"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool = False

    class Config:
        from_attributes = True


class PaginationParams(BaseModel):
    """Параметры пагинации"""
    page: int = Field(default=1, ge=1, description="Номер страницы")
    size: int = Field(default=20, ge=1, le=100, description="Размер страницы")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        return self.size


class PaginatedResponse(BaseModel):
    """Пагинированный ответ"""
    total: int
    page: int
    size: int
    pages: int
    items: list

    class Config:
        from_attributes = True
