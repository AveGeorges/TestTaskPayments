# Система выплат (Payout System)

REST API для управления заявками на выплату с асинхронной обработкой через Celery.

## Технологии

- **Python 3.12**
- **Django 5.1** + Django REST Framework
- **Celery 5.6** — асинхронная обработка задач
- **Redis** — брокер сообщений для Celery
- **PostgreSQL** — база данных

---

## Инструкция по запуску

### 1. Установка зависимостей

```bash
git clone <repository-url>
cd TestTaskPayments

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r req.txt
```

### 2. Настройка переменных окружения

Создайте файл `.env`:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DJANGO_ENV=development
DATABASE_URL=postgresql://user:password@localhost:5432/payout_db
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000
CORS_ALLOWED_ORIGINS=http://localhost:8000
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 3. Запуск миграций

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Запуск Redis

```bash
# Windows (Docker)
docker run -d -p 6379:6379 --name redis redis:alpine

# Linux/Mac
redis-server
```

### 5. Запуск приложения

**Терминал 1 — Django:**
```bash
python manage.py runserver
```

**Терминал 2 — Celery:**
```bash
celery -A core worker -l info -P solo
```

### 6. Запуск тестов

```bash
python manage.py test payments
```

**Доступ:**
- API: http://localhost:8000/api/v1/docs/
- Admin: http://localhost:8000/admin/

**Подробнее:** `docs/LOCAL_SETUP_AND_TESTING.md`

---

## Деплой в продакшн

### Представление деплоя

**Архитектура:**
```
Nginx (reverse proxy, SSL) 
  → Docker Compose
    → web (Gunicorn + Django, 4+ workers)
    → celery (Celery Workers, 4+ workers)
    → db (PostgreSQL 13+)
    → redis (Redis 7+, broker + cache)
    → flower (Celery monitoring, опционально)
```

**Деплой:** Автоматический через CI/CD (GitHub Actions) при push в `main` или создании тега `v*`.

### Необходимые сервисы

1. **Docker** + **Docker Compose** — контейнеризация
2. **PostgreSQL 13+** — основная база данных (в контейнере)
3. **Redis 7+** — брокер для Celery и кэш (в контейнере)
4. **Gunicorn** — WSGI сервер для Django (в контейнере)
5. **Celery Workers** — обработка фоновых задач (в контейнере)
6. **Nginx** — reverse proxy, SSL termination (на хосте или в контейнере)

### Запуск Django и Celery в реальной системе

**Через Docker Compose:**

```yaml
# docker-compose.yml
services:
  web:
    build: .
    command: gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 4
    depends_on:
      - db
      - redis
  
  celery:
    build: .
    command: celery -A core worker --loglevel=info --concurrency=4
    depends_on:
      - db
      - redis
```

**Управление:**
```bash
# Запуск всех сервисов
docker-compose up -d

# Остановка
docker-compose down

# Просмотр логов
docker-compose logs -f

# Перезапуск после обновления
docker-compose up -d --build
```

### Минимальные шаги по подготовке окружения

1. **Установка Docker и Docker Compose:**
   ```bash
   sudo apt install docker.io docker-compose
   sudo systemctl enable docker
   sudo systemctl start docker
   ```

2. **Клонирование репозитория:**
   ```bash
   git clone <repository-url> /opt/payout/app
   cd /opt/payout/app
   ```

3. **Настройка .env:**
   ```env
   DEBUG=False
   DJANGO_ENV=production
   SECRET_KEY=<generate-new-key>
   DATABASE_URL=postgresql://payout_user:password@db:5432/payout_db
   ALLOWED_HOSTS=yourdomain.com
   CELERY_BROKER_URL=redis://redis:6379/0
   CELERY_RESULT_BACKEND=redis://redis:6379/0
   ```

4. **Первый запуск:**
   ```bash
   docker-compose up -d
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py collectstatic --noinput
   docker-compose exec web python manage.py createsuperuser
   ```

5. **Настройка Nginx (на хосте):**
   ```nginx
   upstream payout {
       server 127.0.0.1:8000;  # Порт из docker-compose
   }
   server {
       listen 80;
       server_name yourdomain.com;
       location / {
           proxy_pass http://payout;
       }
   }
   ```

6. **SSL (Let's Encrypt):**
   ```bash
   sudo certbot --nginx -d yourdomain.com
   ```

### CI/CD деплой

**Автоматический деплой через GitHub Actions:**

- При push в `main` → автоматический деплой
- При создании тега `v*` → деплой версии
- Ручной деплой через GitHub UI (выбор версии)

**Процесс:**
1. CI запускает тесты и линтеры
2. При успехе → CD подключается к серверу по SSH
3. Обновляет код, пересобирает контейнеры
4. Перезапускает `docker-compose up -d --build`
5. Проверяет health check

**Подробнее:** `docs/CD_SETUP.md` и `docs/DEPLOYMENT_GUIDE.md`

---

## API Endpoints

- `GET /api/v1/payouts/` — список заявок
- `POST /api/v1/payouts/` — создание заявки
- `GET /api/v1/payouts/{uuid}/` — получение заявки
- `PATCH /api/v1/payouts/{uuid}/` — обновление заявки
- `DELETE /api/v1/payouts/{uuid}/` — удаление заявки
- `GET /api/v1/health/` — health check

Документация: http://localhost:8000/api/v1/docs/

---

## Документация

- **`docs/LOCAL_SETUP_AND_TESTING.md`** — локальный запуск и тестирование
- **`docs/DEPLOYMENT_GUIDE.md`** — подробное руководство по деплою
- **`docs/CD_SETUP.md`** — настройка CI/CD
- **`docs/PAYOUT_FLOW.md`** — путь заявки через систему
- **`docs/DATABASE_OPTIMIZATION.md`** — оптимизация БД
- **`docs/PROFILING_AND_MONITORING.md`** — профилирование и мониторинг
