from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_pagination_params
from app.crud import booking, time_slot
from app.schemas.booking import (
    BookingCreate, BookingUpdate, BookingResponse, BookingWithDetails,
    BookingConfirm, BookingCancel
)
from app.schemas.base import PaginationParams, PaginatedResponse
from app.models.booking import BookingStatus
from app.core.exceptions import (
    SlotNotFoundException, SlotAlreadyBookedException,
    BookingNotFoundException, BookingAlreadyConfirmedException
)

router = APIRouter()


@router.get("/", response_model=PaginatedResponse)
async def get_bookings(
    pagination: PaginationParams = Depends(get_pagination_params),
    status: Optional[BookingStatus] = Query(None, description="Статус бронирования"),
    db: AsyncSession = Depends(get_db)
):
    """Получить список бронирований"""
    filters = {}
    if status:
        filters['status'] = status

    result = await booking.get_multi(db, pagination, filters)
    return result


@router.get("/{booking_id:int}", response_model=BookingResponse)
async def get_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить бронирование по ID"""
    db_booking = await booking.get(db, booking_id)
    if not db_booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return db_booking


@router.get("/{booking_id:int}/details", response_model=BookingWithDetails)
async def get_booking_with_details(
    booking_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить бронирование с деталями"""
    db_booking = await booking.get_with_details(db, booking_id)
    if not db_booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return db_booking


@router.post("/", response_model=BookingResponse)
async def create_booking(
    booking_in: BookingCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создать бронирование"""
    try:
        # Проверяем, что слот существует и доступен
        db_slot = await time_slot.get(db, booking_in.time_slot_id)
        if not db_slot:
            raise SlotNotFoundException("Slot not found")

        if not db_slot.is_available:
            raise SlotAlreadyBookedException("Slot is not available")

        # Создаем бронирование
        db_booking = await booking.create_booking(db, booking_in)

        # Обновляем слот (увеличиваем current_bookings)
        await time_slot.book_slot(db, booking_in.time_slot_id)

        return db_booking
    except (SlotNotFoundException, SlotAlreadyBookedException) as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{booking_id:int}/confirm", response_model=BookingResponse)
async def confirm_booking(
    booking_id: int,
    confirm_data: BookingConfirm,
    db: AsyncSession = Depends(get_db)
):
    """Подтвердить бронирование"""
    try:
        db_booking = await booking.confirm_booking(
            db, booking_id, confirm_data.teacher_notes
        )
        return db_booking
    except (BookingNotFoundException, BookingAlreadyConfirmedException) as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/{booking_id:int}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: int,
    cancel_data: BookingCancel,
    db: AsyncSession = Depends(get_db)
):
    """Отменить бронирование"""
    try:
        db_booking = await booking.cancel_booking(
            db, booking_id, cancel_data.reason
        )

        # Обновляем слот (уменьшаем current_bookings)
        await time_slot.unbook_slot(db, db_booking.time_slot_id)

        return db_booking
    except BookingNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{booking_id:int}/complete", response_model=BookingResponse)
async def complete_booking(
    booking_id: int,
    complete_data: BookingConfirm,
    db: AsyncSession = Depends(get_db)
):
    """Завершить бронирование"""
    try:
        db_booking = await booking.complete_booking(
            db, booking_id, complete_data.teacher_notes
        )
        return db_booking
    except BookingNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/teacher/{teacher_id}/bookings", response_model=List[BookingResponse])
async def get_teacher_bookings(
    teacher_id: int,
    start_date: Optional[datetime] = Query(None, description="Начальная дата"),
    end_date: Optional[datetime] = Query(None, description="Конечная дата"),
    status: Optional[BookingStatus] = Query(None, description="Статус бронирования"),
    db: AsyncSession = Depends(get_db)
):
    """Получить бронирования преподавателя"""
    bookings = await booking.get_teacher_bookings(
        db, teacher_id, start_date, end_date, status
    )
    return bookings


@router.get("/student/{student_id}/bookings", response_model=List[BookingResponse])
async def get_student_bookings(
    student_id: int,
    status: Optional[BookingStatus] = Query(None, description="Статус бронирования"),
    db: AsyncSession = Depends(get_db)
):
    """Получить бронирования студента"""
    bookings = await booking.get_student_bookings(db, student_id, status)
    return bookings


@router.get("/stats", response_model=dict)
async def get_booking_stats(
    teacher_id: Optional[int] = Query(None, description="ID преподавателя"),
    start_date: Optional[datetime] = Query(None, description="Начальная дата"),
    end_date: Optional[datetime] = Query(None, description="Конечная дата"),
    db: AsyncSession = Depends(get_db)
):
    """Получить статистику бронирований"""
    stats = await booking.get_booking_stats(db, teacher_id, start_date, end_date)
    return stats
