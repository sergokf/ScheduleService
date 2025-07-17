from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db
from app.schemas.teacher import TeacherRegister, TeacherLogin
from app.schemas.student import StudentRegister, StudentLogin
from app.models.teacher import Teacher
from app.models.student import Student
from app.core.auth import hash_password, verify_password, create_access_token
from sqlalchemy import select

router = APIRouter()

# Регистрация учителя
def get_teacher_by_slug_or_email(db: AsyncSession, slug_or_email: str):
    query = select(Teacher).where(
        (Teacher.slug == slug_or_email) | (Teacher.email == slug_or_email),
        Teacher.is_deleted == False
    )
    return db.execute(query)

@router.post('/teacher/register')
async def register_teacher(data: TeacherRegister, db: AsyncSession = Depends(get_db)):
    # Проверка уникальности email и slug
    existing = await db.execute(select(Teacher).where((Teacher.email == data.email) | (Teacher.slug == data.slug), Teacher.is_deleted == False))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Учитель с таким email или slug уже существует")
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
    existing = await db.execute(select(Student).where((Student.email == data.email) | (Student.slug == data.slug), Student.is_deleted == False))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Студент с таким email или slug уже существует")
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