# Система выплат (Payout System)

REST API для управления заявками на выплату с асинхронной обработкой через Celery.

## Технологии

- **Python 3.12**
- **Django 5.1** + Django REST Framework
- **Celery 5.6** — асинхронная обработка задач
- **Redis** — брокер сообщений для Celery
- **PostgreSQL** — база данных
- **drf-spectacular** — документация API (Swagger)
- **django-unfold** - админка unfold Django

---

## Быстрый старт

### 1. Клонирование и настройка окружения

```bash
git clone <repository-url>
cd TestTaskPayments

# Создание виртуального окружения
python -m venv .venv

# Активация (Windows)
.venv\Scripts\activate

# Активация (Linux/Mac)
source .venv/bin/activate

# Установка зависимостей
pip install -r req.txt
```

### 2. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DJANGO_ENV=development

# База данных
DATABASE_URL=postgresql://user:password@host/db_name?ATOMIC_REQUESTS=True

# Настройки доступа
ALLOWED_HOSTS=localhost,127.0.0.1,[::1]
CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000
```

### 3. Настройка базы данных

```bash
# Создайте базу данных PostgreSQL
# Затем примените миграции:
python manage.py migrate

# Создайте суперпользователя
python manage.py createsuperuser
```

### 4. Запуск Redis

**Windows (через Docker):**
```bash
docker run -d -p 6379:6379 --name redis redis:alpine
```

**Linux/Mac:**
```bash
redis-server
```

### 5. Запуск проекта

Откройте **3 терминала**:

**Терминал 1 — Django сервер:**
```bash
python manage.py runserver
```

**Терминал 2 — Celery worker:**
```bash
celery -A core worker -l info -P solo
```

**Терминал 3 — (опционально) дополнительные workers для параллельной обработки:**
```bash
celery -A core worker -l info -P solo -n worker2
```

---

## Использование API

### Swagger документация

После запуска откройте: **http://127.0.0.1:8000/api/v1/docs/**

### Авторизация

1. Войдите в Django Admin: **http://127.0.0.1:8000/admin/**
2. Вернитесь в Swagger — сессия будет активна

Или используйте **Basic Auth**:
- Нажмите кнопку **Authorize** в Swagger
- Введите логин/пароль суперпользователя

### Endpoints

| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/api/v1/payouts/` | Список заявок |
| POST | `/api/v1/payouts/` | Создание заявки |
| GET | `/api/v1/payouts/{uuid}/` | Получение заявки |
| PATCH | `/api/v1/payouts/{uuid}/` | Обновление статуса |
| DELETE | `/api/v1/payouts/{uuid}/` | Удаление заявки |

### Пример создания заявки

```json
{
  "amount": "1500.00",
  "currency": "RUB",
  "recipient_details": {
    "type": "card",
    "number": "4111111111111111",
    "holder": "Иван Иванов"
  },
  "description": "Тестовая выплата"
}
```

### Фильтрация и сортировка

```
GET /api/v1/payouts/?status=pending
GET /api/v1/payouts/?currency=RUB
GET /api/v1/payouts/?ordering=-created_at
GET /api/v1/payouts/?ordering=amount
```

---

## Архитектура

### Структура проекта

```
TestTaskPayments/
├── core/                   # Настройки Django
│   ├── settings.py
│   ├── celery.py          # Конфигурация Celery
│   └── urls.py
├── payments/              # Приложение выплат
│   ├── models.py          # Модель PayoutRequest
│   ├── views.py           # API ViewSet
│   ├── serializers.py     # Сериализаторы
│   ├── services.py        # Бизнес-логика
│   ├── tasks.py           # Celery задачи
│   ├── signals.py         # Django сигналы
│   └── tests.py           # Тесты
└── req.txt
```

### Поток обработки заявки

```
1. POST /api/v1/payouts/
   ↓
2. Django создаёт заявку (status: pending)
   ↓
3. Signal отправляет задачу в Celery (после commit)
   ↓
4. API возвращает 201 Created (мгновенно)
   ↓
5. Celery worker получает задачу
   ↓
6. PayoutService обрабатывает:
   - Меняет статус на "processing"
   - Валидирует реквизиты
   - Отправляет в платёжный шлюз (имитация)
   - Меняет статус на "completed" или "failed"
```

### Статусы заявки

| Статус | Описание |
|--------|----------|
| `pending` | Ожидает обработки |
| `processing` | В обработке |
| `completed` | Выполнена успешно |
| `failed` | Ошибка |
| `cancelled` | Отменена |

---

## Тестирование

### Запуск всех тестов

```bash
python manage.py test payments
```

### Запуск отдельных тестов

```bash
# Тесты модели
python manage.py test payments.tests.PayoutRequestModelTest

# Тесты API
python manage.py test payments.tests.PayoutAPITest

# Тесты сервисов
python manage.py test payments.tests.PayoutServiceTest
```

### Что тестируется

- ✅ Создание заявки через API
- ✅ Вызов Celery задачи при создании
- ✅ Валидация данных (amount, recipient_details)
- ✅ Получение/обновление/удаление по UUID
- ✅ Запрет удаления заявок в статусе "processing"
- ✅ Доступ только для админов
- ✅ Бизнес-логика сервисного слоя

---

## Проверка асинхронной обработки

### 1. Запустите несколько workers

```bash
# Терминал 1
celery -A core worker -l info -P solo -n worker1

# Терминал 2
celery -A core worker -l info -P solo -n worker2

# Терминал 3
celery -A core worker -l info -P solo -n worker3
```

### 2. Создайте несколько заявок быстро

Используйте Swagger для быстрого создания 5-10 заявок подряд.

### 3. Наблюдайте за логами

**Django** — мгновенные ответы:
```
INFO "POST /api/v1/payouts/" 201
INFO "POST /api/v1/payouts/" 201
INFO "POST /api/v1/payouts/" 201
```

**Celery workers** — параллельная обработка:
```
[worker1] Task received... обработка e89d617e
[worker2] Task received... обработка dbadcc94  ← параллельно!
[worker3] Task received... обработка 70eba8d9  ← параллельно!
```

---

## Особенности реализации

### Защита от race conditions

- `select_for_update()` — блокировка строки при обновлении
- `transaction.atomic()` — атомарные транзакции
- `transaction.on_commit()` — отправка задачи только после коммита

### Асинхронность

- **Django → Celery** — API не ждёт обработки (главный эффект)
- **Несколько workers** — параллельная обработка очереди
- **asyncio внутри задачи** — неблокирующие I/O операции

### Безопасность

- `IsAdminUser` — доступ только для администраторов
- `SessionAuthentication` + `BasicAuthentication`
- CSRF защита для сессий

---

## Полезные команды

```bash
# Запуск сервера
python manage.py runserver

# Celery worker
celery -A core worker -l info -P solo

# Миграции
python manage.py makemigrations
python manage.py migrate

# Тесты
python manage.py test payments

# Создание суперпользователя
python manage.py createsuperuser

# Django shell
python manage.py shell
```

---

## Возможные проблемы

### Redis не запущен
```
Error connecting to localhost:6379
```
**Решение:** Запустите Redis через Docker или Memurai.

### Ошибка CSRF
```
CSRF Failed: CSRF token incorrect
```
**Решение:** Обновите страницу Swagger (F5) или используйте Basic Auth.

### База данных занята
```
database "test_tt_payments" is being accessed by other users
```
**Решение:** Перезапустите PostgreSQL или используйте `--keepdb`.
