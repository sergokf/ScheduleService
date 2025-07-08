from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.student import Student
from app.schemas.student import StudentCreate, StudentUpdate


class CRUDStudent(CRUDBase[Student, StudentCreate, StudentUpdate]):
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[Student]:
        """Получить студента по email"""
        query = select(self.model).where(
            self.model.email == email,
            self.model.is_deleted == False
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_active_students(self, db: AsyncSession) -> List[Student]:
        """Получить активных студентов"""
        query = select(self.model).where(
            self.model.is_active == True,
            self.model.is_deleted == False
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_with_bookings(self, db: AsyncSession, student_id: int) -> Optional[Student]:
        """Получить студента с бронированиями"""
        query = select(self.model).options(
            selectinload(self.model.bookings)
        ).where(
            self.model.id == student_id,
            self.model.is_deleted == False
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()


student = CRUDStudent(Student)
