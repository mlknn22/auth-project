# Auth System API

Система аутентификации и авторизации на FastAPI + PostgreSQL.

## Технологии

- FastAPI — веб-фреймворк
- PostgreSQL — база данных
- SQLAlchemy (async) — ORM
- bcrypt — хеширование паролей
- PyJWT — работа с JWT-токенами
- Pydantic — валидация данных
- uv — менеджер зависимостей

## Запуск

### 1. Клонировать репозиторий
git clone https://github.com/mlknn22/auth-project
cd auth-project

### 2. Установить зависимости
uv sync

### 3. Создать базу данных
createdb auth_db

Или через psql:
CREATE DATABASE auth_db;

### 4. Настроить переменные окружения

Создать файл `.env` в корне проекта:

DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/auth_db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

### 5. Запустить приложение

uv run uvicorn app.main:app --reload

Приложение будет доступно на http://localhost:8000

Документация API: http://localhost:8000/docs

## Тестовый пользователь

При первом запуске создаётся администратор:
- Email: admin@example.com
- Пароль: admin123

## Схема базы данных

### Таблица users

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer, PK | Уникальный идентификатор |
| first_name | String(100) | Имя |
| last_name | String(100) | Фамилия |
| patronymic | String(100), nullable | Отчество |
| email | String(255), unique | Email (используется для логина) |
| hashed_password | String(255) | Хеш пароля (bcrypt) |
| is_active | Boolean | Активен ли аккаунт (мягкое удаление) |
| role_id | Integer, FK → roles.id | Ссылка на роль |
| created_at | DateTime | Дата создания |
| updated_at | DateTime | Дата обновления |

### Таблица roles

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer, PK | Уникальный идентификатор |
| name | String(50), unique | Название роли |
| description | String(255), nullable | Описание |

### Таблица business_elements

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer, PK | Уникальный идентификатор |
| code | String(50), unique | Код элемента (products, orders, shops) |
| name | String(100) | Название |
| description | String(255), nullable | Описание |

### Таблица access_rules

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer, PK | Уникальный идентификатор |
| role_id | Integer, FK → roles.id | Ссылка на роль |
| element_id | Integer, FK → business_elements.id | Ссылка на ресурс |
| read_permission | Boolean | Чтение своих объектов |
| read_all_permission | Boolean | Чтение всех объектов |
| create_permission | Boolean | Создание объектов |
| update_permission | Boolean | Обновление своих объектов |
| update_all_permission | Boolean | Обновление всех объектов |
| delete_permission | Boolean | Удаление своих объектов |
| delete_all_permission | Boolean | Удаление всех объектов |

Уникальное ограничение: пара (role_id, element_id) — одно правило для каждой комбинации.

## Схема разграничения прав доступа (RBAC)

Используется модель Role-Based Access Control:
```
User ──> Role ──> AccessRule <── BusinessElement
```

Каждый пользователь имеет одну роль. Для каждой пары (роль, ресурс) задано правило с набором разрешений.

Разрешения делятся на «свои» и «все»:
- read / read_all — чтение своих объектов / всех объектов
- update / update_all — обновление своих / всех
- delete / delete_all — удаление своих / всех
- create — создание (не делится, объект всегда «свой»)

### Матрица прав по умолчанию

| Роль | Ресурс | read | read_all | create | update | update_all | delete | delete_all |
|------|--------|------|----------|--------|--------|------------|--------|------------|
| admin | products | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| admin | shops | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| admin | orders | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| manager | products | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| manager | shops | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| manager | orders | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| user | products | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| user | shops | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| user | orders | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ | ✗ |
| guest | products | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| guest | shops | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| guest | orders | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

Администратор может изменять эти правила через API (эндпоинты /admin/).

## Аутентификация

Используется JWT (JSON Web Token):

1. Пользователь отправляет email + пароль на POST /auth/login
2. Сервер проверяет пароль (bcrypt) и выдаёт JWT-токен
3. Клиент прикладывает токен к каждому запросу в заголовке: Authorization: Bearer <token>
4. Сервер декодирует токен, извлекает user_id и загружает пользователя из БД

Пароли хранятся в виде bcrypt-хешей. Токен содержит только user_id и срок действия.

## API эндпоинты

### Аутентификация

- POST /auth/register — регистрация
- POST /auth/login — вход (возвращает JWT-токен)
- POST /auth/logout — выход
- GET /auth/me — профиль текущего пользователя
- PUT /auth/me — обновление профиля
- DELETE /auth/me — мягкое удаление аккаунта

### Администрирование (только admin)

- GET /admin/roles — список ролей
- POST /admin/roles — создать роль
- GET /admin/elements — список бизнес-элементов
- POST /admin/elements — создать бизнес-элемент
- GET /admin/access-rules — список правил доступа
- POST /admin/access-rules — создать правило
- PUT /admin/access-rules/{id} — обновить правило
- DELETE /admin/access-rules/{id} — удалить правило
- PUT /admin/users/{id}/role?role_id=N — назначить роль пользователю

### Бизнес-ресурсы (mock)

- GET /api/products — список товаров
- POST /api/products — создать товар
- GET /api/shops — список магазинов
- POST /api/shops — создать магазин
- GET /api/orders — список заказов
- POST /api/orders — создать заказ

Доступ к ресурсам определяется ролью пользователя и правилами в таблице access_rules.