from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.teacher import Teacher
from app.schemas.teacher import TeacherCreate, TeacherUpdate


class CRUDTeacher(CRUDBase[Teacher, TeacherCreate, TeacherUpdate]):
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[Teacher]:
        """Получить преподавателя по email"""
        query = select(self.model).where(
            self.model.email == email,
            self.model.is_deleted == False
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_active_teachers(self, db: AsyncSession) -> List[Teacher]:
        """Получить активных преподавателей"""
        query = select(self.model).where(
            self.model.is_active == True,
            self.model.is_deleted == False
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_with_slots(self, db: AsyncSession, teacher_id: int) -> Optional[Teacher]:
        """Получить преподавателя со слотами"""
        query = select(self.model).options(
            selectinload(self.model.time_slots)
        ).where(
            self.model.id == teacher_id,
            self.model.is_deleted == False
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()


teacher = CRUDTeacher(Teacher)
