from .teachers import router as teachers_router
from .students import router as students_router
from .slots import router as slots_router
from .bookings import router as bookings_router

__all__ = [
    "teachers_router",
    "students_router",
    "slots_router",
    "bookings_router"
]
