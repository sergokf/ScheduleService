from fastapi import HTTPException
from starlette import status


class BaseCustomException(HTTPException):
    """Базовый класс для кастомных исключений"""
    def __init__(self, detail: str = None):
        super().__init__(status_code=self.status_code, detail=detail or self.detail)


class SlotNotFoundException(BaseCustomException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Slot not found"


class SlotAlreadyBookedException(BaseCustomException):
    status_code = status.HTTP_409_CONFLICT
    detail = "Slot is already booked"


class SlotOverlapException(BaseCustomException):
    status_code = status.HTTP_409_CONFLICT
    detail = "Slot overlaps with existing slot"


class BookingNotFoundException(BaseCustomException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Booking not found"


class BookingAlreadyConfirmedException(BaseCustomException):
    status_code = status.HTTP_409_CONFLICT
    detail = "Booking is already confirmed"


class BookingAlreadyCancelledException(BaseCustomException):
    status_code = status.HTTP_409_CONFLICT
    detail = "Booking is already cancelled"


class TeacherNotFoundException(BaseCustomException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Teacher not found"


class StudentNotFoundException(BaseCustomException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Student not found"


class InvalidTimeSlotException(BaseCustomException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Invalid time slot: end time must be after start time"


class SlotInPastException(BaseCustomException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Cannot create slot in the past"
