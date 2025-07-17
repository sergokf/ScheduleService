from fastapi import APIRouter

from app.api.v1.endpoints import (
    teachers_router,
    students_router,
    slots_router,
    bookings_router
)
from app.api.v1.endpoints.auth import router as auth_router

api_router = APIRouter()

# Подключаем роутеры endpoints
api_router.include_router(
    teachers_router,
    prefix="/teachers",
    tags=["teachers"]
)

api_router.include_router(
    students_router,
    prefix="/students", 
    tags=["students"]
)

api_router.include_router(
    slots_router,
    prefix="/slots",
    tags=["slots"]
)

api_router.include_router(
    bookings_router,
    prefix="/bookings",
    tags=["bookings"]
)

api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["auth"]
)
