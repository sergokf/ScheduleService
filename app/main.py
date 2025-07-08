import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import init_db, close_db, check_db_connection
from app.api.v1 import api_router
from app.core.exceptions import BaseCustomException

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения"""
    # Startup
    logger.info("Starting up application...")

    # Инициализация базы данных
    try:
        await init_db()

        # Проверка соединения с БД
        if await check_db_connection():
            logger.info("✅ Database connection successful")
        else:
            logger.error("❌ Database connection failed")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    await close_db()


# Создание приложения
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Микросервис календаря для платформы учителей",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Настройка CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Глобальный обработчик исключений
@app.exception_handler(BaseCustomException)
async def custom_exception_handler(request, exc: BaseCustomException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Проверка состояния сервиса"""
    try:
        db_status = await check_db_connection()
        return {
            "status": "healthy" if db_status else "unhealthy",
            "database": "connected" if db_status else "disconnected",
            "version": settings.APP_VERSION
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy", 
                "database": "error",
                "error": str(e)
            }
        )


# Подключение API роутеров
app.include_router(api_router, prefix=settings.API_V1_STR)


# Root endpoint
@app.get("/")
async def root():
    """Корневая точка API"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
