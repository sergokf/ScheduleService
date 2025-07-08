from typing import Generator, Optional
from fastapi import Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.schemas.base import PaginationParams


async def get_db() -> Generator[AsyncSession, None, None]:
    """Получить сессию базы данных"""
    async for session in get_async_session():
        yield session


def get_pagination_params(
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(20, ge=1, le=100, description="Размер страницы")
) -> PaginationParams:
    """Получить параметры пагинации"""
    return PaginationParams(page=page, size=size)


def get_optional_int(
    value: Optional[int] = Query(None, ge=1)
) -> Optional[int]:
    """Получить опциональное целое число"""
    return value
