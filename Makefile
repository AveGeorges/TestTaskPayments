.PHONY: help install migrate runserver worker test lint format clean docker-up docker-down docker-build

help: ## Показать справку по командам
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Установить зависимости
	pip install -r req.txt

migrate: ## Применить миграции
	python manage.py migrate

makemigrations: ## Создать миграции
	python manage.py makemigrations

runserver: ## Запустить Django сервер
	python manage.py runserver

worker: ## Запустить Celery worker
	celery -A core worker -l info -P solo

worker-beat: ## Запустить Celery beat (для периодических задач)
	celery -A core beat -l info

flower: ## Запустить Flower (мониторинг Celery)
	celery -A core flower

test: ## Запустить тесты
	python manage.py test payments

test-coverage: ## Запустить тесты с покрытием
	coverage run --source='.' manage.py test payments
	coverage report
	coverage html

lint: ## Проверить код линтером (flake8)
	flake8 . --exclude=migrations,venv,.venv,__pycache__ --max-line-length=120

format: ## Отформатировать код (black)
	black . --exclude=migrations,venv,.venv

format-check: ## Проверить форматирование без изменений
	black --check . --exclude=migrations,venv,.venv

type-check: ## Проверить типы (mypy)
	mypy payments --ignore-missing-imports --no-strict-optional

check: lint format-check type-check ## Запустить все проверки

createsuperuser: ## Создать суперпользователя
	python manage.py createsuperuser

shell: ## Открыть Django shell
	python manage.py shell

collectstatic: ## Собрать статические файлы
	python manage.py collectstatic --noinput

docker-up: ## Запустить Docker Compose
	docker-compose up -d

docker-down: ## Остановить Docker Compose
	docker-compose down

docker-build: ## Собрать Docker образы
	docker-compose build

docker-logs: ## Показать логи Docker
	docker-compose logs -f

docker-restart: ## Перезапустить Docker контейнеры
	docker-compose restart

clean: ## Очистить временные файлы
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/

setup: install migrate createsuperuser ## Полная настройка проекта (установка + миграции + суперпользователь)
