# type: ignore
# pyright: reportGeneralTypeIssues=false
# pylance: reportGeneralTypeIssues=false
# flake8: noqa
# pylint: skip-file
from typing import Optional, List
from datetime import datetime, time, timedelta, timezone
from sqlalchemy import select, and_, or_, text, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import uuid
from app.core.config import get_settings

from app.crud.base import CRUDBase
from app.models.time_slot import TimeSlot, SlotStatus
from app.schemas.time_slot import TimeSlotCreate, TimeSlotUpdate, BulkSlotCreate
from app.core.exceptions import SlotOverlapException, SlotNotFoundException


def to_naive_utc(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


class CRUDTimeSlot(CRUDBase[TimeSlot, TimeSlotCreate, TimeSlotUpdate]):
    async def get_available_slots(
        self, 
        db: AsyncSession, 
        teacher_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[TimeSlot]:
        """Получить доступные слоты"""
        if start_date:
            start_date = to_naive_utc(start_date)
        if end_date:
            end_date = to_naive_utc(end_date)
        query = select(self.model).where(
            self.model.status == SlotStatus.AVAILABLE,
            self.model.is_deleted == False,
            self.model.current_bookings < self.model.max_students
        )

        if teacher_id:
            query = query.where(self.model.teacher_id == teacher_id)

        if start_date:
            query = query.where(self.model.start_time >= start_date)

        if end_date:
            query = query.where(self.model.end_time <= end_date)

        query = query.order_by(self.model.start_time)
        result = await db.execute(query)
        return result.scalars().all()

    async def check_slot_overlap(
        self, 
        db: AsyncSession, 
        teacher_id: int,
        start_time: datetime,
        end_time: datetime,
        exclude_slot_id: Optional[int] = None
    ) -> bool:
        """Проверить пересечение слотов"""
        start_time = to_naive_utc(start_time)
        end_time = to_naive_utc(end_time)
        query = select(self.model).where(
            self.model.teacher_id == teacher_id,
            self.model.is_deleted == False,
            # Проверка пересечения: новый слот пересекается с существующим если:
            # start_time < existing_end_time И end_time > existing_start_time
            and_(
                self.model.start_time < end_time,
                self.model.end_time > start_time
            )
        )

        if exclude_slot_id:
            query = query.where(self.model.id != exclude_slot_id)

        result = await db.execute(query)
        return result.scalar_one_or_none() is not None

    async def create_with_overlap_check(
        self, 
        db: AsyncSession, 
        obj_in: TimeSlotCreate
    ) -> TimeSlot:
        """Создать слот с проверкой пересечения"""
        # Проверяем пересечение
        has_overlap = await self.check_slot_overlap(
            db, obj_in.teacher_id, obj_in.start_time, obj_in.end_time
        )

        if has_overlap:
            raise SlotOverlapException("Slot overlaps with existing slot")

        return await self.create(db, obj_in)

    async def create(
        self,
        db: AsyncSession,
        obj_in: TimeSlotCreate
    ) -> TimeSlot:
        settings = get_settings()
        unique_name = str(uuid.uuid4())
        meeting_url = f"{settings.SERVER_URL}/{unique_name}"
        # Привести start_time и end_time к naive UTC
        start_time = to_naive_utc(obj_in.start_time)
        end_time = to_naive_utc(obj_in.end_time)
        data = obj_in.model_dump()
        data["start_time"] = start_time
        data["end_time"] = end_time
        data["meeting_url"] = meeting_url
        db_obj = self.model(**data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def create_bulk_slots(
        self, 
        db: AsyncSession, 
        bulk_data: BulkSlotCreate
    ) -> List[TimeSlot]:
        """Массовое создание слотов"""
        slots_to_create = []
        current_date = bulk_data.start_date.date()
        end_date = bulk_data.end_date.date()

        # Парсим время
        start_time = datetime.strptime(bulk_data.start_time, "%H:%M").time()
        end_time = datetime.strptime(bulk_data.end_time, "%H:%M").time()

        while current_date <= end_date:
            # Проверяем, что это нужный день недели
            if current_date.weekday() in bulk_data.days_of_week:
                slot_start = datetime.combine(current_date, start_time)
                slot_end = datetime.combine(current_date, end_time)

                # Проверяем пересечение
                has_overlap = await self.check_slot_overlap(
                    db, bulk_data.teacher_id, slot_start, slot_end
                )

                if not has_overlap:
                    slot_data = TimeSlotCreate(
                        teacher_id=bulk_data.teacher_id,
                        start_time=slot_start,
                        end_time=slot_end,
                        max_students=bulk_data.max_students,
                        description=bulk_data.description,
                        price=bulk_data.price
                    )
                    slots_to_create.append(slot_data)

            current_date += timedelta(days=1)

        # Создаем слоты
        created_slots = []
        for slot_data in slots_to_create:
            slot = await self.create(db, slot_data)
            created_slots.append(slot)

        return created_slots

    async def book_slot(
        self, 
        db: AsyncSession, 
        slot_id: int
    ) -> TimeSlot:
        """Забронировать слот (увеличить current_bookings)"""
        # Используем advisory lock для предотвращения race condition
        await db.execute(text("SELECT pg_advisory_xact_lock(:slot_id)"), {"slot_id": slot_id})

        slot = await self.get(db, slot_id)
        if not slot:
            raise SlotNotFoundException("Slot not found")

        if slot.current_bookings >= slot.max_students:
            raise SlotOverlapException("Slot is already full")

        # Увеличиваем количество бронирований
        slot.current_bookings += 1

        # Если слот заполнен, меняем статус
        if slot.current_bookings >= slot.max_students:
            slot.status = SlotStatus.BOOKED

        await db.commit()
        await db.refresh(slot)
        return slot

    async def unbook_slot(
        self, 
        db: AsyncSession, 
        slot_id: int
    ) -> TimeSlot:
        """Отменить бронирование слота (уменьшить current_bookings)"""
        # Используем advisory lock для предотвращения race condition
        await db.execute(text("SELECT pg_advisory_xact_lock(:slot_id)"), {"slot_id": slot_id})

        slot = await self.get(db, slot_id)
        if not slot:
            raise SlotNotFoundException("Slot not found")

        if slot.current_bookings > 0:
            slot.current_bookings -= 1

        # Если слот освободился, меняем статус на доступный
        if slot.current_bookings < slot.max_students and slot.status == SlotStatus.BOOKED:
            slot.status = SlotStatus.AVAILABLE

        await db.commit()
        await db.refresh(slot)
        return slot

    async def get_teacher_schedule(
        self, 
        db: AsyncSession, 
        teacher_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[TimeSlot]:
        """Получить расписание преподавателя"""
        query = select(self.model).options(
            selectinload(self.model.bookings)
        ).where(
            self.model.teacher_id == teacher_id,
            self.model.is_deleted == False
        )

        if start_date:
            query = query.where(self.model.start_time >= start_date)

        if end_date:
            query = query.where(self.model.end_time <= end_date)

        query = query.order_by(self.model.start_time)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_with_details(self, db: AsyncSession, slot_id: int) -> Optional[TimeSlot]:
        query = select(self.model).options(
            selectinload(self.model.teacher),
            selectinload(self.model.bookings)
        ).where(self.model.id == slot_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()


time_slot = CRUDTimeSlot(TimeSlot)
