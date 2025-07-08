import pytest

pytestmark = pytest.mark.asyncio

from httpx import AsyncClient
import uuid
from datetime import datetime, timedelta


class TestTeachersAPI:
    pytestmark = pytest.mark.asyncio
    """Тесты API преподавателей"""

    async def test_create_teacher(self, client: AsyncClient):
        teacher_data = {
            "name": "John Doe",
            "email": f"john_{uuid.uuid4()}@example.com",
            "phone": "+1234567890",
            "bio": "Experienced teacher"
        }

        response = await client.post("/api/v1/teachers/", json=teacher_data)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["name"] == teacher_data["name"]
        assert data["email"] == teacher_data["email"]
        assert "id" in data

    async def test_get_teacher(self, client: AsyncClient, test_teacher):
        response = await client.get(f"/api/v1/teachers/{test_teacher['id']}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == test_teacher["id"]
        assert data["name"] == test_teacher["name"]

    async def test_get_nonexistent_teacher(self, client: AsyncClient):
        response = await client.get("/api/v1/teachers/99999")
        assert response.status_code == 404

    async def test_update_teacher(self, client: AsyncClient, test_teacher):
        update_data = {"name": "Updated Teacher", "bio": "Updated bio"}
        response = await client.put(f"/api/v1/teachers/{test_teacher['id']}", json=update_data)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["name"] == "Updated Teacher"
        assert data["bio"] == "Updated bio"

    async def test_delete_teacher(self, client: AsyncClient, test_teacher):
        response = await client.delete(f"/api/v1/teachers/{test_teacher['id']}")
        assert response.status_code == 200, response.text
        # Проверяем, что повторное получение возвращает 404
        response = await client.get(f"/api/v1/teachers/{test_teacher['id']}")
        assert response.status_code == 404

    async def test_get_teacher_with_slots(self, client: AsyncClient, test_teacher, test_time_slot):
        response = await client.get(f"/api/v1/teachers/{test_teacher['id']}/with-slots")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["id"] == test_teacher["id"]
        assert isinstance(data["time_slots"], list)
        assert any(slot["id"] == test_time_slot["id"] for slot in data["time_slots"])

    async def test_get_active_teachers(self, client: AsyncClient):
        response = await client.get("/api/v1/teachers/active/list")
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)


class TestStudentsAPI:
    pytestmark = pytest.mark.asyncio
    """Тесты API студентов"""

    async def test_create_student(self, client: AsyncClient):
        student_data = {
            "name": "Jane Smith",
            "email": f"jane_{uuid.uuid4()}@example.com",
            "phone": "+0987654321"
        }

        response = await client.post("/api/v1/students/", json=student_data)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["name"] == student_data["name"]
        assert data["email"] == student_data["email"]

    async def test_get_student(self, client: AsyncClient, test_student):
        response = await client.get(f"/api/v1/students/{test_student['id']}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == test_student["id"]
        assert data["name"] == test_student["name"]

    async def test_update_student(self, client: AsyncClient, test_student):
        update_data = {"name": "Updated Student"}
        response = await client.put(f"/api/v1/students/{test_student['id']}", json=update_data)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["name"] == "Updated Student"

    async def test_delete_student(self, client: AsyncClient, test_student):
        response = await client.delete(f"/api/v1/students/{test_student['id']}")
        assert response.status_code == 200, response.text
        # Проверяем, что повторное получение возвращает 404
        response = await client.get(f"/api/v1/students/{test_student['id']}")
        assert response.status_code == 404

    async def test_get_student_with_bookings(self, client: AsyncClient, test_student, test_time_slot):
        # Создаем бронирование для студента
        booking_data = {
            "time_slot_id": test_time_slot["id"],
            "student_id": test_student["id"]
        }
        response = await client.post("/api/v1/bookings/", json=booking_data)
        assert response.status_code == 200, response.text
        response = await client.get(f"/api/v1/students/{test_student['id']}/with-bookings")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["id"] == test_student["id"]
        assert isinstance(data["bookings"], list)
        assert any(b["time_slot_id"] == test_time_slot["id"] for b in data["bookings"])

    async def test_get_active_students(self, client: AsyncClient):
        response = await client.get("/api/v1/students/active/list")
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)


class TestSlotsAPI:
    pytestmark = pytest.mark.asyncio
    """Тесты API слотов"""

    async def test_create_slot(self, client: AsyncClient, test_teacher):
        now = datetime.utcnow()
        slot_data = {
            "teacher_id": test_teacher["id"],
            "start_time": (now + timedelta(days=1)).isoformat(),
            "end_time": (now + timedelta(days=1, hours=1)).isoformat(),
            "max_students": 1,
            "description": "Test lesson"
        }

        response = await client.post("/api/v1/slots/", json=slot_data)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["teacher_id"] == test_teacher["id"]
        assert data["description"] == slot_data["description"]

    async def test_get_available_slots(self, client: AsyncClient, test_time_slot):
        response = await client.get("/api/v1/slots/available")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_create_overlapping_slot(self, client: AsyncClient, test_teacher, test_time_slot):
        assert "id" in test_time_slot, f"Slot creation failed: {test_time_slot}"
        # Пытаемся создать слот, который пересекается с существующим
        slot_data = {
            "teacher_id": test_teacher["id"],
            "start_time": test_time_slot["start_time"],
            "end_time": test_time_slot["end_time"],
            "max_students": 1
        }

        response = await client.post("/api/v1/slots/", json=slot_data)
        assert response.status_code == 409  # Conflict

    async def test_bulk_create_slots(self, client: AsyncClient, test_teacher):
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        dt_str = lambda d: d.strftime("%Y-%m-%dT00:00:00")
        bulk_data = {
            "teacher_id": test_teacher["id"],
            "start_date": dt_str(now + timedelta(days=2)),
            "end_date": dt_str(now + timedelta(days=2)),
            "start_time": "10:00",
            "end_time": "11:00",
            "days_of_week": [ (now + timedelta(days=2)).weekday() ],
            "max_students": 2,
            "description": "Bulk slot",
            "price": 100.0
        }
        response = await client.post("/api/v1/slots/bulk", json=bulk_data)
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        slot_id = data[0]["id"]
        # Проверяем получение по id
        response = await client.get(f"/api/v1/slots/{slot_id}")
        assert response.status_code == 200, response.text
        # Проверяем получение с деталями
        response = await client.get(f"/api/v1/slots/{slot_id}/details")
        assert response.status_code == 200, response.text
        # Проверяем обновление
        update_data = {"description": "Updated bulk slot"}
        response = await client.put(f"/api/v1/slots/{slot_id}", json=update_data)
        assert response.status_code == 200, response.text
        assert response.json()["description"] == "Updated bulk slot"
        # Проверяем удаление
        response = await client.delete(f"/api/v1/slots/{slot_id}")
        assert response.status_code == 200, response.text
        # Проверяем, что после удаления слот не доступен по id
        response = await client.get(f"/api/v1/slots/{slot_id}")
        assert response.status_code == 404

    async def test_teacher_schedule_and_availability(self, client: AsyncClient, test_teacher, test_time_slot):
        # Проверяем расписание
        response = await client.get(f"/api/v1/slots/teacher/{test_teacher['id']}/schedule")
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)
        # Проверяем доступность
        response = await client.get(f"/api/v1/slots/teacher/{test_teacher['id']}/availability")
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)


class TestBookingsAPI:
    pytestmark = pytest.mark.asyncio
    """Тесты API бронирований"""

    async def test_create_booking(self, client: AsyncClient, test_time_slot, test_student):
        assert "id" in test_time_slot, f"Slot creation failed: {test_time_slot}"
        booking_data = {
            "time_slot_id": test_time_slot["id"],
            "student_id": test_student["id"],
            "student_notes": "Looking forward to the lesson"
        }

        response = await client.post("/api/v1/bookings/", json=booking_data)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["time_slot_id"] == test_time_slot["id"]
        assert data["student_id"] == test_student["id"]
        assert data["status"] == "pending"

    async def test_confirm_booking(self, client: AsyncClient, test_time_slot, test_student):
        assert "id" in test_time_slot, f"Slot creation failed: {test_time_slot}"
        # Сначала создаем бронирование
        booking_data = {
            "time_slot_id": test_time_slot["id"],
            "student_id": test_student["id"]
        }

        response = await client.post("/api/v1/bookings/", json=booking_data)
        assert response.status_code == 200, response.text
        booking_id = response.json()["id"]

        # Подтверждаем бронирование
        confirm_data = {
            "teacher_notes": "Confirmed by teacher"
        }

        response = await client.post(f"/api/v1/bookings/{booking_id}/confirm", json=confirm_data)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["status"] == "confirmed"
        assert data["teacher_notes"] == "Confirmed by teacher"

    async def test_cancel_booking(self, client: AsyncClient, test_time_slot, test_student):
        assert "id" in test_time_slot, f"Slot creation failed: {test_time_slot}"
        # Сначала создаем бронирование
        booking_data = {
            "time_slot_id": test_time_slot["id"],
            "student_id": test_student["id"]
        }

        response = await client.post("/api/v1/bookings/", json=booking_data)
        assert response.status_code == 200, response.text
        booking_id = response.json()["id"]

        # Отменяем бронирование
        cancel_data = {
            "reason": "Student cancelled"
        }

        response = await client.post(f"/api/v1/bookings/{booking_id}/cancel", json=cancel_data)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["status"] == "cancelled"

    async def test_get_booking_by_id(self, client: AsyncClient, test_time_slot, test_student):
        # Создаем бронирование
        booking_data = {
            "time_slot_id": test_time_slot["id"],
            "student_id": test_student["id"]
        }
        response = await client.post("/api/v1/bookings/", json=booking_data)
        assert response.status_code == 200, response.text
        booking_id = response.json()["id"]
        # Получение по id
        response = await client.get(f"/api/v1/bookings/{booking_id}")
        assert response.status_code == 200, response.text
        # Получение с деталями
        response = await client.get(f"/api/v1/bookings/{booking_id}/details")
        assert response.status_code == 200, response.text

    async def test_complete_booking(self, client: AsyncClient, test_time_slot, test_student):
        # Создаем и подтверждаем бронирование
        booking_data = {
            "time_slot_id": test_time_slot["id"],
            "student_id": test_student["id"]
        }
        response = await client.post("/api/v1/bookings/", json=booking_data)
        assert response.status_code == 200, response.text
        booking_id = response.json()["id"]
        response = await client.post(f"/api/v1/bookings/{booking_id}/confirm", json={})
        assert response.status_code == 200, response.text
        # Завершаем бронирование
        response = await client.post(f"/api/v1/bookings/{booking_id}/complete", json={"teacher_notes": "Done"})
        assert response.status_code == 200, response.text
        assert response.json()["status"] == "completed"

    async def test_teacher_bookings(self, client: AsyncClient, test_teacher, test_time_slot, test_student):
        # Создаем бронирование
        booking_data = {
            "time_slot_id": test_time_slot["id"],
            "student_id": test_student["id"]
        }
        response = await client.post("/api/v1/bookings/", json=booking_data)
        assert response.status_code == 200, response.text
        # Получаем бронирования преподавателя
        response = await client.get(f"/api/v1/bookings/teacher/{test_teacher['id']}/bookings")
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)
        assert any(b["time_slot_id"] == test_time_slot["id"] for b in data)

    async def test_student_bookings(self, client: AsyncClient, test_student, test_time_slot):
        # Создаем бронирование
        booking_data = {
            "time_slot_id": test_time_slot["id"],
            "student_id": test_student["id"]
        }
        response = await client.post("/api/v1/bookings/", json=booking_data)
        assert response.status_code == 200, response.text
        # Получаем бронирования студента
        response = await client.get(f"/api/v1/bookings/student/{test_student['id']}/bookings")
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)
        assert any(b["time_slot_id"] == test_time_slot["id"] for b in data)

    async def test_booking_stats(self, client: AsyncClient):
        response = await client.get("/api/v1/bookings/stats")
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, dict)


class TestHealthCheck:
    pytestmark = pytest.mark.asyncio
    """Тесты health check"""

    async def test_health_endpoint(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "version" in data

    async def test_root_endpoint(self, client: AsyncClient):
        response = await client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "version" in data
