from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_pagination_params
from app.crud import time_slot
from app.schemas.time_slot import (
    TimeSlotCreate, TimeSlotUpdate, TimeSlotResponse, TimeSlotWithDetails,
    BulkSlotCreate
)
from app.schemas.base import PaginationParams, PaginatedResponse
from app.core.exceptions import SlotOverlapException

router = APIRouter()


@router.get("/", response_model=PaginatedResponse)
async def get_slots(
    pagination: PaginationParams = Depends(get_pagination_params),
    teacher_id: Optional[int] = Query(None, description="ID преподавателя"),
    start_date: Optional[datetime] = Query(None, description="Начальная дата"),
    end_date: Optional[datetime] = Query(None, description="Конечная дата"),
    db: AsyncSession = Depends(get_db)
):
    """Получить список всех слотов"""
    filters = {}
    if teacher_id:
        filters['teacher_id'] = teacher_id

    result = await time_slot.get_multi(db, pagination, filters)
    return result


@router.get("/available", response_model=List[TimeSlotResponse])
async def get_available_slots(
    teacher_id: Optional[int] = Query(None, description="ID преподавателя"),
    start_date: Optional[datetime] = Query(None, description="Начальная дата"),
    end_date: Optional[datetime] = Query(None, description="Конечная дата"),
    db: AsyncSession = Depends(get_db)
):
    """Получить доступные слоты"""
    slots = await time_slot.get_available_slots(db, teacher_id, start_date, end_date)
    return slots


@router.get("/{slot_id}", response_model=TimeSlotResponse)
async def get_slot(
    slot_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить слот по ID"""
    db_slot = await time_slot.get(db, slot_id)
    if not db_slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    return db_slot


@router.get("/{slot_id}/details", response_model=TimeSlotWithDetails)
async def get_slot_with_details(
    slot_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить слот с деталями (учитель и бронирования)"""
    db_slot = await time_slot.get_with_details(db, slot_id)
    if not db_slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    return db_slot


@router.post("/", response_model=TimeSlotResponse)
async def create_slot(
    slot_in: TimeSlotCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создать новый слот"""
    try:
        db_slot = await time_slot.create_with_overlap_check(db, slot_in)
        return db_slot
    except SlotOverlapException as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/bulk", response_model=List[TimeSlotResponse])
async def create_bulk_slots(
    bulk_data: BulkSlotCreate,
    db: AsyncSession = Depends(get_db)
):
    """Массовое создание слотов"""
    try:
        slots = await time_slot.create_bulk_slots(db, bulk_data)
        return slots
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{slot_id}", response_model=TimeSlotResponse)
async def update_slot(
    slot_id: int,
    slot_update: TimeSlotUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Обновить слот"""
    db_slot = await time_slot.get(db, slot_id)
    if not db_slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    # Проверяем пересечение при обновлении времени
    if slot_update.start_time or slot_update.end_time:
        start_time = slot_update.start_time or db_slot.start_time
        end_time = slot_update.end_time or db_slot.end_time

        has_overlap = await time_slot.check_slot_overlap(
            db, db_slot.teacher_id, start_time, end_time, exclude_slot_id=slot_id
        )

        if has_overlap:
            raise HTTPException(status_code=409, detail="Slot overlaps with existing slot")

    updated_slot = await time_slot.update(db, db_slot, slot_update)
    return updated_slot


@router.delete("/{slot_id}")
async def delete_slot(
    slot_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Удалить слот"""
    db_slot = await time_slot.get(db, slot_id)
    if not db_slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    # Проверяем, что слот не забронирован
    if db_slot.current_bookings > 0:
        raise HTTPException(status_code=400, detail="Cannot delete slot with active bookings")

    success = await time_slot.delete(db, slot_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete slot")

    return {"message": "Slot deleted successfully"}


@router.get("/teacher/{teacher_id}/schedule", response_model=List[TimeSlotResponse])
async def get_teacher_schedule(
    teacher_id: int,
    start_date: Optional[datetime] = Query(None, description="Начальная дата"),
    end_date: Optional[datetime] = Query(None, description="Конечная дата"),
    db: AsyncSession = Depends(get_db)
):
    """Получить расписание преподавателя"""
    schedule = await time_slot.get_teacher_schedule(db, teacher_id, start_date, end_date)
    return schedule


@router.get("/teacher/{teacher_id}/availability", response_model=List[TimeSlotResponse])
async def get_teacher_availability(
    teacher_id: int,
    start_date: Optional[datetime] = Query(None, description="Начальная дата"),
    end_date: Optional[datetime] = Query(None, description="Конечная дата"),
    db: AsyncSession = Depends(get_db)
):
    """Получить доступность преподавателя"""
    available_slots = await time_slot.get_available_slots(db, teacher_id, start_date, end_date)
    return available_slots
