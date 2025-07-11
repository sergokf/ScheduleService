from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel
from datetime import datetime, timezone

from app.models.base import BaseModel
from app.schemas.base import PaginationParams, PaginatedResponse

ModelType = TypeVar("ModelType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=SQLModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=SQLModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD базовый класс с типизацией
        """
        self.model = model

    async def get(self, db: AsyncSession, id: int) -> Optional[ModelType]:
        """Получить объект по ID"""
        query = select(self.model).where(
            self.model.id == id,
            self.model.is_deleted == False
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(
        self, 
        db: AsyncSession, 
        pagination: PaginationParams,
        filters: dict = None
    ) -> PaginatedResponse:
        """Получить список объектов с пагинацией"""
        query = select(self.model).where(self.model.is_deleted == False)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    query = query.where(getattr(self.model, key) == value)

        # Подсчет общего количества
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Применение пагинации
        query = query.offset(pagination.offset).limit(pagination.limit)
        result = await db.execute(query)
        items = result.scalars().all()

        return PaginatedResponse(
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=(total + pagination.size - 1) // pagination.size,
            items=items
        )

    async def create(self, db: AsyncSession, obj_in: CreateSchemaType) -> ModelType:
        """Создать новый объект"""
        obj_data = obj_in.dict()
        # Приводим все datetime к naive UTC
        for k, v in obj_data.items():
            if isinstance(v, datetime) and v.tzinfo is not None:
                obj_data[k] = v.astimezone(timezone.utc).replace(tzinfo=None)
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, 
        db: AsyncSession, 
        db_obj: ModelType, 
        obj_in: UpdateSchemaType
    ) -> ModelType:
        """Обновить объект"""
        obj_data = obj_in.dict(exclude_unset=True)
        for field, value in obj_data.items():
            # Приводим datetime к naive UTC только для datetime
            if isinstance(value, datetime):
                if value.tzinfo is not None:
                    value = value.astimezone(timezone.utc).replace(tzinfo=None)
                else:
                    value = value.replace(tzinfo=None)
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, id: int) -> bool:
        """Мягкое удаление объекта"""
        query = (
            update(self.model)
            .where(self.model.id == id)
            .values(is_deleted=True)
        )
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0

    async def remove(self, db: AsyncSession, id: int) -> bool:
        """Жесткое удаление объекта"""
        query = delete(self.model).where(self.model.id == id)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0
