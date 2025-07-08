# type: ignore
# pyright: reportGeneralTypeIssues=false
# pylance: reportGeneralTypeIssues=false
# flake8: noqa
# pylint: skip-file
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.expression import false
from sqlmodel import SQLModel

from app.crud.base import CRUDBase
from app.models.booking import Booking, BookingStatus
from app.schemas.booking import BookingCreate, BookingUpdate
from app.core.exceptions import (
    BookingNotFoundException, 
    BookingAlreadyConfirmedException,
    BookingAlreadyCancelledException,
    SlotAlreadyBookedException
)
from app.models.time_slot import TimeSlot


class CRUDBooking(CRUDBase[Booking, BookingCreate, BookingUpdate]):  # type: ignore
    async def create_booking(
        self, 
        db: AsyncSession, 
        obj_in: BookingCreate
    ) -> Booking:
        """Создать бронирование"""
        # Проверяем, что студент еще не забронировал этот слот
        existing_booking = await self.get_student_slot_booking(
            db, obj_in.student_id, obj_in.time_slot_id
        )

        if existing_booking and existing_booking.status != BookingStatus.CANCELLED:
            raise SlotAlreadyBookedException("Student already booked this slot")

        # Создаем бронирование
        booking_data = obj_in.dict()
        booking_data['booking_time'] = datetime.utcnow()
        booking_data['status'] = BookingStatus.PENDING

        db_booking = self.model(**booking_data)
        db.add(db_booking)
        await db.commit()
        await db.refresh(db_booking)
        return db_booking

    async def get_student_slot_booking(
        self, 
        db: AsyncSession, 
        student_id: int, 
        slot_id: int
    ) -> Optional[Booking]:
        """Получить бронирование студента для конкретного слота"""
        query = select(self.model).where(
            self.model.student_id == student_id,
            self.model.time_slot_id == slot_id,
            self.model.is_deleted == False  # type: ignore
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def confirm_booking(
        self, 
        db: AsyncSession, 
        booking_id: int, 
        teacher_notes: Optional[str] = None
    ) -> Booking:
        """Подтвердить бронирование"""
        booking = await self.get(db, booking_id)
        if not booking:
            raise BookingNotFoundException("Booking not found")

        if booking.status == BookingStatus.CONFIRMED:
            raise BookingAlreadyConfirmedException("Booking is already confirmed")

        if booking.status == BookingStatus.CANCELLED:
            raise BookingAlreadyCancelledException("Cannot confirm cancelled booking")

        booking.status = BookingStatus.CONFIRMED
        booking.confirmed_at = datetime.utcnow()
        if teacher_notes:
            booking.teacher_notes = teacher_notes

        await db.commit()
        await db.refresh(booking)
        return booking

    async def cancel_booking(
        self, 
        db: AsyncSession, 
        booking_id: int, 
        reason: Optional[str] = None
    ) -> Booking:
        """Отменить бронирование"""
        booking = await self.get(db, booking_id)
        if not booking:
            raise BookingNotFoundException("Booking not found")

        if booking.status == BookingStatus.CANCELLED:
            raise BookingAlreadyCancelledException("Booking is already cancelled")

        booking.status = BookingStatus.CANCELLED
        booking.cancelled_at = datetime.utcnow()
        if reason:
            booking.teacher_notes = reason

        await db.commit()
        await db.refresh(booking)
        return booking

    async def complete_booking(
        self, 
        db: AsyncSession, 
        booking_id: int, 
        teacher_notes: Optional[str] = None
    ) -> Booking:
        """Завершить бронирование"""
        booking = await self.get(db, booking_id)
        if not booking:
            raise BookingNotFoundException("Booking not found")

        if booking.status != BookingStatus.CONFIRMED:
            raise BookingAlreadyConfirmedException("Can only complete confirmed bookings")

        booking.status = BookingStatus.COMPLETED
        booking.completed_at = datetime.utcnow()
        if teacher_notes:
            booking.teacher_notes = teacher_notes

        await db.commit()
        await db.refresh(booking)
        return booking

    async def get_teacher_bookings(
        self, 
        db: AsyncSession, 
        teacher_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[BookingStatus] = None
    ) -> List[Booking]:
        """Получить бронирования преподавателя"""
        query = select(self.model).options(
            selectinload(self.model.time_slot).selectinload(TimeSlot.teacher),
            selectinload(self.model.student)
        ).join(
            self.model.time_slot
        ).where(
            self.model.time_slot.has(teacher_id=teacher_id),
            self.model.is_deleted == False  # type: ignore
        )

        if status:
            query = query.where(self.model.status == status)

        if start_date:
            query = query.where(self.model.time_slot.has(start_time__gte=start_date))

        if end_date:
            query = query.where(self.model.time_slot.has(end_time__lte=end_date))

        query = query.order_by(self.model.booking_time.desc())
        result = await db.execute(query)
        return result.scalars().all()

    async def get_student_bookings(
        self, 
        db: AsyncSession, 
        student_id: int,
        status: Optional[BookingStatus] = None
    ) -> List[Booking]:
        """Получить бронирования студента"""
        query = select(self.model).options(
            selectinload(self.model.time_slot).selectinload(TimeSlot.teacher),
            selectinload(self.model.student)
        ).where(
            self.model.student_id == student_id,
            self.model.is_deleted == False  # type: ignore
        )

        if status:
            query = query.where(self.model.status == status)

        query = query.order_by(self.model.booking_time.desc())
        result = await db.execute(query)
        return result.scalars().all()

    async def get_booking_stats(
        self, 
        db: AsyncSession, 
        teacher_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """Получить статистику бронирований"""
        query = select(
            self.model.status,
            func.count(self.model.id).label('count')
        ).where(
            self.model.is_deleted == False  # type: ignore
        )

        if teacher_id:
            query = query.join(self.model.time_slot).where(
                self.model.time_slot.has(teacher_id=teacher_id)
            )

        if start_date:
            query = query.where(self.model.booking_time >= start_date)

        if end_date:
            query = query.where(self.model.booking_time <= end_date)

        query = query.group_by(self.model.status)
        result = await db.execute(query)

        stats = {status.value: 0 for status in BookingStatus}
        for row in result:
            stats[row.status] = row.count

        return stats

    async def get_with_details(self, db: AsyncSession, booking_id: int) -> Optional[Booking]:
        query = select(self.model).options(
            selectinload(self.model.time_slot),
            selectinload(self.model.student)
        ).where(self.model.id == booking_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()


booking = CRUDBooking(Booking)
