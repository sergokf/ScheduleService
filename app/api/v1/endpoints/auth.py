from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db
from app.schemas.teacher import TeacherRegister, TeacherLogin
from app.schemas.student import StudentRegister, StudentLogin
from app.models.teacher import Teacher
from app.models.student import Student
from app.core.auth import hash_password, verify_password, create_access_token, teacher_required, student_required
from sqlalchemy import select, and_
from app.crud.teacher import teacher as teacher_crud
from app.crud.student import student as student_crud
from sqlalchemy.sql.expression import false as sa_false
from pydantic import BaseModel, Field

router = APIRouter()

# Регистрация учителя
def get_teacher_by_slug_or_email(db: AsyncSession, slug_or_email: str):
    query = select(Teacher).where(
        (Teacher.slug == slug_or_email) | (Teacher.email == slug_or_email),
        Teacher.is_deleted == False
    )
    return db.execute(query)

class PasswordChangeRequest(BaseModel):
    old_password: str = Field(..., min_length=6, max_length=128)
    new_password: str = Field(..., min_length=6, max_length=128)

@router.post('/teacher/register')
async def register_teacher(data: TeacherRegister, db: AsyncSession = Depends(get_db)):
    # Проверка уникальности email
    existing_email = await db.execute(select(Teacher).where((Teacher.email == data.email) & (Teacher.is_deleted == False)))
    if existing_email.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Teacher with this email already exists")
    # Проверка уникальности slug
    existing_slug = await db.execute(select(Teacher).where((Teacher.slug == data.slug) & (Teacher.is_deleted == False)))
    if existing_slug.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Teacher with this slug already exists")
    teacher = Teacher(
        name=data.name,
        email=data.email,
        phone=data.phone,
        bio=data.bio,
        slug=data.slug,
        password_hash=hash_password(data.password)
    )
    db.add(teacher)
    await db.commit()
    await db.refresh(teacher)
    token = create_access_token({"sub": str(teacher.id), "role": "teacher", "slug": teacher.slug, "email": teacher.email})
    return {"access_token": token, "token_type": "bearer"}

@router.post('/teacher/login')
async def login_teacher(data: TeacherLogin, db: AsyncSession = Depends(get_db)):
    query = select(Teacher).where(
        ((Teacher.slug == data.slug_or_email) | (Teacher.email == data.slug_or_email)),
        Teacher.is_deleted == False
    )
    result = await db.execute(query)
    teacher = result.scalar_one_or_none()
    if not teacher or not teacher.password_hash or not verify_password(data.password, teacher.password_hash):
        raise HTTPException(status_code=401, detail="Неверные данные для входа")
    token = create_access_token({"sub": str(teacher.id), "role": "teacher", "slug": teacher.slug, "email": teacher.email})
    return {"access_token": token, "token_type": "bearer"}

# Регистрация студента
@router.post('/student/register')
async def register_student(data: StudentRegister, db: AsyncSession = Depends(get_db)):
    existing_email = await db.execute(select(Student).where((Student.email == data.email) & (Student.is_deleted == False)))
    if existing_email.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Студент с таким email уже существует")
    existing_slug = await db.execute(select(Student).where((Student.slug == data.slug) & (Student.is_deleted == False)))
    if existing_slug.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Студент с таким slug уже существует")
    student = Student(
        name=data.name,
        email=data.email,
        phone=data.phone,
        slug=data.slug,
        password_hash=hash_password(data.password)
    )
    db.add(student)
    await db.commit()
    await db.refresh(student)
    token = create_access_token({"sub": str(student.id), "role": "student", "slug": student.slug, "email": student.email})
    return {"access_token": token, "token_type": "bearer"}

@router.post('/student/login')
async def login_student(data: StudentLogin, db: AsyncSession = Depends(get_db)):
    query = select(Student).where(
        ((Student.slug == data.slug_or_email) | (Student.email == data.slug_or_email)),
        Student.is_deleted == False
    )
    result = await db.execute(query)
    student = result.scalar_one_or_none()
    if not student or not student.password_hash or not verify_password(data.password, student.password_hash):
        raise HTTPException(status_code=401, detail="Неверные данные для входа")
    token = create_access_token({"sub": str(student.id), "role": "student", "slug": student.slug, "email": student.email})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/teacher/change-password")
async def change_teacher_password(
    data: PasswordChangeRequest,
    current=Depends(teacher_required),
    db: AsyncSession = Depends(get_db)
):
    teacher_id = int(current["sub"])
    db_teacher = await teacher_crud.get(db, teacher_id)
    if not db_teacher or not db_teacher.password_hash or not verify_password(data.old_password, db_teacher.password_hash):
        raise HTTPException(status_code=400, detail="Старый пароль неверен")
    db_teacher.password_hash = hash_password(data.new_password)
    await db.commit()
    return {"message": "Пароль успешно изменён"}

@router.post("/student/change-password")
async def change_student_password(
    data: PasswordChangeRequest,
    current=Depends(student_required),
    db: AsyncSession = Depends(get_db)
):
    student_id = int(current["sub"])
    db_student = await student_crud.get(db, student_id)
    if not db_student or not db_student.password_hash or not verify_password(data.old_password, db_student.password_hash):
        raise HTTPException(status_code=400, detail="Старый пароль неверен")
    db_student.password_hash = hash_password(data.new_password)
    await db.commit()
    return {"message": "Пароль успешно изменён"} 