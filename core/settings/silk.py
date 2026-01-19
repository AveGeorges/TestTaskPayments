"""
Настройки Django Silk для профилирования запросов.

Django Silk - инструмент для профилирования Django приложений.
Позволяет отслеживать:
- SQL запросы и их время выполнения
- HTTP запросы и ответы
- Время выполнения views
- Использование памяти
- Профилирование кода (cProfile)

ВАЖНО: Используется только в development окружении!
"""

import environ

env = environ.Env()

# Включаем Silk только в development
SILKY_ENABLED = env("DJANGO_ENV") == "development"

if SILKY_ENABLED:
    # Настройки Silk
    SILKY_PYTHON_PROFILER = True  # Включаем Python profiler
    SILKY_PYTHON_PROFILER_BINARY = True  # Сохраняем бинарные профили
    
    # Настройки для анализа SQL запросов
    SILKY_ANALYZE_QUERIES = True  # Анализ SQL запросов
    
    # Настройки для фильтрации запросов
    SILKY_META = True  # Сохранять метаданные запросов
    
    # Настройки для интерфейса
    SILKY_INTERCEPT_PERCENT = 100  # Профилировать 100% запросов (можно уменьшить для production-like тестов)
    
    # Настройки для производительности
    SILKY_MAX_RECORDED_REQUESTS = 10000  # Максимум записей в БД
    SILKY_MAX_RECORDED_REQUESTS_CHECK_PERCENT = 10  # Проверять каждые 10%
    
    # Настройки для аутентификации (опционально)
    # SILKY_AUTHENTICATION = True  # Требовать авторизацию
    # SILKY_AUTHORISATION = True  # Требовать права доступа
    # SILKY_PERMISSIONS = lambda user: user.is_staff  # Только для staff
    
    # Настройки для игнорирования определённых путей
    SILKY_IGNORE_PATHS = [
        '/silk/',
        '/admin/jsi18n/',
        '/static/',
        '/media/',
    ]
    
    # Настройки для логирования
    SILKY_LOG_LEVEL = 'INFO'  # Уровень логирования
