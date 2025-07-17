# Schedule Microservice 📅

Микросервис календаря для платформы учителей - система управления расписанием и бронирования временных слотов.

## 🎯 Описание

Этот микросервис предоставляет RESTful API для управления календарем преподавателей, где:
- Преподаватели создают временные слоты без привязки к конкретному предмету
- Студенты могут записываться на любые доступные слоты
- Система автоматически предотвращает двойное бронирование
- Занятые слоты исчезают из списка доступных

## 🏗️ Архитектура

### Технологический стек
- **FastAPI** - современный веб-фреймворк для Python
- **SQLModel** - типобезопасный ORM на основе SQLAlchemy 2.0
- **PostgreSQL** - надежная реляционная база данных
- **Alembic** - система миграций базы данных
- **Docker** - контейнеризация для простого развертывания
- **Pytest** - фреймворк тестирования

### Основные компоненты
```
app/
├── api/v1/           # API endpoints
├── core/             # Конфигурация и зависимости
├── crud/             # CRUD операции
├── models/           # SQLModel модели
└── schemas/          # Pydantic схемы
```

## 🚀 Быстрый старт

### Запуск с Docker (рекомендуется)

1. **Клонируйте проект:**
```bash
git clone <repository>
cd schedule_microservice
```

2. **(Опционально) Очистите БД для чистого старта:**
```bash
docker-compose down -v
```

3. **Запустите сервисы:**
```bash
docker-compose up --build
```

- При запуске автоматически:
  - Ждём готовности БД (wait-for-it.sh)
  - Применяются все миграции Alembic
  - Запускается FastAPI-приложение

4. **Проверьте работу:**
- API документация: http://localhost:8000/docs
- Health check: http://localhost:8000/health

> **Примечание:** Для ручного тестирования используйте уникальные email (например, с uuid) и создавайте слоты только с будущим временем.

### Локальная разработка

1. **Создайте виртуальное окружение:**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows
```

2. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

3. **Настройте базу данных:**
```bash
# Создайте базу данных PostgreSQL
createdb schedule_db

# Выполните миграции
alembic upgrade head
```

4. **Запустите приложение:**
```bash
uvicorn app.main:app --reload
```

## 📖 API Документация

### Преподаватели (`/api/v1/teachers`)
- `GET /` - список преподавателей
- `POST /` - создание преподавателя
- `GET /me` - получение авторизованного преподавателя
- `GET /{id}` - получение преподавателя
- `PUT /{id}` - обновление преподавателя
- `DELETE /{id}` - удаление преподавателя
- `GET /{id}/with-slots` - получение преподавателя со слотами
- `GET /active/list` - получение активных преподавателей

### Студенты (`/api/v1/students`)
- `GET /` - список студентов
- `POST /` - создание студента
- `GET /me` - получение авторизованного студента
- `GET /{id}` - получение студента
- `PUT /{id}` - обновление студента
- `DELETE /{id}` - удаление студента
- `GET /{id}/with-bookings` - получение студента с бронированиями
- `GET /active/list` - получение активных студентов

### Временные слоты (`/api/v1/slots`)
- `GET /` - список слотов
- `GET /available` - доступные слоты
- `POST /` - создание слота
- `GET /{id}` - информация о слоте
- `PUT /{id}` - обновление слота
- `DELETE /{id}` - удаление слота
- `GET /{id}/details` - подробная информация о слоте
- `GET /teacher/{id}/schedule` - получение информации о слотах учителя
- `GET /teacher/{id}/availability` - получение информации о доступных слотах учителя

### Бронирования (`/api/v1/bookings`)
- `GET /` - получение бронирований
- `POST /` - создание бронирования
- `GET /{id}` - получение бронирования
- `GET /{id}/details` - получение подробной информации о бронировании
- `POST /{id}/confirm` - подтверждение бронирования
- `POST /{id}/cancel` - отмена бронирования
- `POST /{id}/complete` - завершение бронирования
- `GET /teacher/{id}/bookings` - получение бронирований преподавателя
- `GET /student/{id}/bookings` - получение бронирований стундента
- `GET /stats` - статистика бронирований


#### Как работает авторизация

- Для доступа к защищённым эндпоинтам используется JWT (JSON Web Token) и схема авторизации HTTP Bearer.
- После регистрации или логина пользователь получает access_token (JWT), который необходимо указывать в заголовке Authorization для всех защищённых запросов.

#### Регистрация и логин

- **Регистрация преподавателя:**
  - `POST /api/v1/auth/teacher/register`
  - В теле запроса: name, email, phone, bio, slug, password
- **Логин преподавателя:**
  - `POST /api/v1/auth/teacher/login`
  - В теле запроса: slug_or_email, password
- **Регистрация студента:**
  - `POST /api/v1/auth/student/register`
  - В теле запроса: name, email, phone, slug, password
- **Логин студента:**
  - `POST /api/v1/auth/student/login`
  - В теле запроса: slug_or_email, password

В ответе на логин/регистрацию приходит:
```json
{
  "access_token": "<JWT>",
  "token_type": "bearer"
}
```

#### Использование токена

- Для доступа к защищённым эндпоинтам (например, `/api/v1/teachers/me`, `/api/v1/students/me`) добавьте заголовок:
  - `Authorization: Bearer <ваш_JWT_токен>`
- В Swagger UI (http://localhost:8000/docs) используйте кнопку **Authorize** и вставьте токен в формате `Bearer <JWT>`.
- Токен действителен 30 минут (можно изменить в настройках).

#### Пример работы через curl

```bash
# Логин
curl -X POST http://localhost:8000/api/v1/auth/teacher/login \
  -H "Content-Type: application/json" \
  -d '{"slug_or_email": "valera", "password": "password123"}'

# Получение профиля
curl -X GET http://localhost:8000/api/v1/teachers/me \
  -H "Authorization: Bearer <ваш_JWT_токен>"
```

#### Особенности
- JWT хранит id, роль, slug, email пользователя и срок действия (exp).
- Для фронтенда: рекомендуется хранить токен в httpOnly cookie или безопасном хранилище.
- Для выхода достаточно удалить токен на клиенте.
- Для продакшена обязательно используйте HTTPS!

#### Best practices
- Не храните токен в localStorage (уязвимо для XSS).
- Не передавайте токен через URL-параметры.
- Используйте CORS и secure cookie для защиты.

---

## 🔧 Конфигурация

### Переменные окружения

```env
# База данных
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Приложение
APP_NAME=Schedule Microservice
DEBUG=true
API_V1_STR=/api/v1

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
```

### Docker Compose

Проект включает готовую конфигурацию Docker Compose с:
- **PostgreSQL 16** с health checks
- **Автоматическим ожиданием готовности БД** (wait-for-it.sh)
- **Автоматическим применением миграций** при запуске
- **Горячей перезагрузкой** для разработки
- **Томами** для персистентности данных

## 🔐 Безопасность

### Предотвращение race conditions
- **PostgreSQL advisory locks** для атомарного бронирования
- **Транзакционная проверка** доступности слотов
- **Валидация пересечений** временных интервалов

### Валидация данных
- **Pydantic схемы** для всех входных данных
- **Проверка временных интервалов** на корректность
- **Уникальность email** для пользователей

## 📊 Мониторинг

### Health Checks
```bash
curl http://localhost:8000/health
```

Возвращает статус:
```json
{
  "status": "healthy",
  "database": "connected", 
  "version": "1.0.0"
}
```

### Логирование
- Структурированные логи
- Различные уровни логирования
- Отслеживание ошибок и производительности

## 🔄 Миграции базы данных

### Создание миграции
```bash
alembic revision --autogenerate -m "Description"
```

### Применение миграций
- **В Docker Compose**: миграции применяются автоматически при запуске.
- **Локально** (если не через Docker):
```bash
alembic upgrade head
```

### Откат миграций
```bash
alembic downgrade -1
```

## 🚀 Развертывание

### Production готовность

Проект включает:
- ✅ **Контейнеризация** с оптимизированным Dockerfile
- ✅ **Health checks** для мониторинга
- ✅ **Graceful shutdown** обработка
- ✅ **Логирование** для production
- ✅ **CORS настройки** для фронтенда
- ✅ **Обработка ошибок** с понятными сообщениями


## 🤝 Разработка

### Структура проекта

```
schedule_microservice/
├── app/                    # Основное приложение
│   ├── api/v1/            # API версии 1
│   ├── core/              # Конфигурация
│   ├── crud/              # CRUD операции
│   ├── models/            # Модели БД
│   └── schemas/           # Pydantic схемы
├── alembic/               # Миграции
├── tests/                 # Тесты
├── docker-compose.yml     # Docker конфигурация
└── requirements.txt       # Python зависимости
```

### Расширение функциональности

Для добавления новых endpoints:

1. Создайте модель в `app/models/`
2. Добавьте схемы в `app/schemas/`
3. Реализуйте CRUD в `app/crud/`
4. Создайте router в `app/api/v1/endpoints/`
5. Подключите в `app/api/v1/router.py`
6. Добавьте тесты в `tests/`
