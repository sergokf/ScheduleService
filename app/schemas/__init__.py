from .base import BaseResponse, PaginationParams, PaginatedResponse
from .teacher import TeacherCreate, TeacherUpdate, TeacherResponse, TeacherWithSlots
from .student import StudentCreate, StudentUpdate, StudentResponse, StudentWithBookings
from .time_slot import (
    TimeSlotCreate, TimeSlotUpdate, TimeSlotResponse, TimeSlotWithDetails,
    BulkSlotCreate
)
from .booking import (
    BookingCreate, BookingUpdate, BookingResponse, BookingWithDetails,
    BookingConfirm, BookingCancel
)

__all__ = [
    "BaseResponse", "PaginationParams", "PaginatedResponse",
    "TeacherCreate", "TeacherUpdate", "TeacherResponse", "TeacherWithSlots",
    "StudentCreate", "StudentUpdate", "StudentResponse", "StudentWithBookings",
    "TimeSlotCreate", "TimeSlotUpdate", "TimeSlotResponse", "TimeSlotWithDetails",
    "BulkSlotCreate",
    "BookingCreate", "BookingUpdate", "BookingResponse", "BookingWithDetails",
    "BookingConfirm", "BookingCancel"
]
