from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_pagination_params
from app.crud import teacher
from app.schemas.teacher import TeacherCreate, TeacherUpdate, TeacherResponse, TeacherWithSlots
from app.schemas.base import PaginationParams, PaginatedResponse

router = APIRouter()


@router.get("/", response_model=PaginatedResponse)
async def get_teachers(
    pagination: PaginationParams = Depends(get_pagination_params),
    is_active: Optional[bool] = Query(None, description="Фильтр по активности"),
    db: AsyncSession = Depends(get_db)
):
    """Получить список преподавателей"""
    filters = {}
    if is_active is not None:
        filters['is_active'] = is_active

    result = await teacher.get_multi(db, pagination, filters)
    return result


@router.get("/{teacher_id}", response_model=TeacherResponse)
async def get_teacher(
    teacher_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить преподавателя по ID"""
    db_teacher = await teacher.get(db, teacher_id)
    if not db_teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return db_teacher


@router.get("/{teacher_id}/with-slots", response_model=TeacherWithSlots)
async def get_teacher_with_slots(
    teacher_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить преподавателя со слотами"""
    db_teacher = await teacher.get_with_slots(db, teacher_id)
    if not db_teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return db_teacher


@router.post("/", response_model=TeacherResponse)
async def create_teacher(
    teacher_in: TeacherCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создать преподавателя"""
    # Проверяем, что email уникален
    existing_teacher = await teacher.get_by_email(db, teacher_in.email)
    if existing_teacher:
        raise HTTPException(status_code=400, detail="Teacher with this email already exists")
    # Проверяем, что slug уникален
    existing_slug = await teacher.get_by_slug(db, teacher_in.slug)
    if existing_slug:
        raise HTTPException(status_code=400, detail="Teacher with this slug already exists")

    db_teacher = await teacher.create(db, teacher_in)
    return db_teacher


@router.put("/{teacher_id}", response_model=TeacherResponse)
async def update_teacher(
    teacher_id: int,
    teacher_update: TeacherUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Обновить преподавателя"""
    db_teacher = await teacher.get(db, teacher_id)
    if not db_teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    # Проверяем email на уникальность, если он изменяется
    if teacher_update.email and teacher_update.email != db_teacher.email:
        existing_teacher = await teacher.get_by_email(db, teacher_update.email)
        if existing_teacher:
            raise HTTPException(status_code=400, detail="Teacher with this email already exists")
    # Проверяем slug на уникальность, если он изменяется
    if teacher_update.slug and teacher_update.slug != db_teacher.slug:
        existing_slug = await teacher.get_by_slug(db, teacher_update.slug)
        if existing_slug:
            raise HTTPException(status_code=400, detail="Teacher with this slug already exists")

    updated_teacher = await teacher.update(db, db_teacher, teacher_update)
    return updated_teacher


@router.delete("/{teacher_id}")
async def delete_teacher(
    teacher_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Удалить преподавателя"""
    db_teacher = await teacher.get(db, teacher_id)
    if not db_teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    success = await teacher.delete(db, teacher_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete teacher")

    return {"message": "Teacher deleted successfully"}


@router.get("/active/list", response_model=List[TeacherResponse])
async def get_active_teachers(
    db: AsyncSession = Depends(get_db)
):
    """Получить список активных преподавателей"""
    teachers = await teacher.get_active_teachers(db)
    return teachers
