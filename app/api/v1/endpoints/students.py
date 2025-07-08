from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_pagination_params
from app.crud import student
from app.schemas.student import StudentCreate, StudentUpdate, StudentResponse, StudentWithBookings
from app.schemas.base import PaginationParams, PaginatedResponse

router = APIRouter()


@router.get("/", response_model=PaginatedResponse)
async def get_students(
    pagination: PaginationParams = Depends(get_pagination_params),
    is_active: Optional[bool] = Query(None, description="Фильтр по активности"),
    db: AsyncSession = Depends(get_db)
):
    """Получить список студентов"""
    filters = {}
    if is_active is not None:
        filters['is_active'] = is_active

    result = await student.get_multi(db, pagination, filters)
    return result


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить студента по ID"""
    db_student = await student.get(db, student_id)
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    return db_student


@router.get("/{student_id}/with-bookings", response_model=StudentWithBookings)
async def get_student_with_bookings(
    student_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить студента с бронированиями"""
    db_student = await student.get_with_bookings(db, student_id)
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    return db_student


@router.post("/", response_model=StudentResponse)
async def create_student(
    student_in: StudentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создать студента"""
    # Проверяем, что email уникален
    existing_student = await student.get_by_email(db, student_in.email)
    if existing_student:
        raise HTTPException(status_code=400, detail="Student with this email already exists")

    db_student = await student.create(db, student_in)
    return db_student


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: int,
    student_update: StudentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Обновить студента"""
    db_student = await student.get(db, student_id)
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Проверяем email на уникальность, если он изменяется
    if student_update.email and student_update.email != db_student.email:
        existing_student = await student.get_by_email(db, student_update.email)
        if existing_student:
            raise HTTPException(status_code=400, detail="Student with this email already exists")

    updated_student = await student.update(db, db_student, student_update)
    return updated_student


@router.delete("/{student_id}")
async def delete_student(
    student_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Удалить студента"""
    db_student = await student.get(db, student_id)
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")

    success = await student.delete(db, student_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete student")

    return {"message": "Student deleted successfully"}


@router.get("/active/list", response_model=List[StudentResponse])
async def get_active_students(
    db: AsyncSession = Depends(get_db)
):
    """Получить список активных студентов"""
    students = await student.get_active_students(db)
    return students
