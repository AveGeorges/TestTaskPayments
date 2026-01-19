"""
Мониторинг подключений к БД и медленных запросов.

Логирует:
- Медленные SQL запросы (> 1 сек)
- Количество активных соединений
- Предупреждения при превышении лимитов
"""

import logging
import time
import environ
from typing import Optional
from django.db import connection
from django.db.backends.utils import CursorWrapper
from django.core.signals import request_started, request_finished
from django.dispatch import receiver

env = environ.Env()
logger = logging.getLogger(__name__)

# Пороги для мониторинга
SLOW_QUERY_THRESHOLD = 1.0  # 1 секунда
MAX_CONNECTIONS_WARNING = 80  # 80% от max_connections
MAX_CONNECTIONS_CRITICAL = 90  # 90% от max_connections


class DatabaseMonitoringMiddleware:
    """
    Middleware для мониторинга медленных запросов к БД.
    
    Логирует все SQL запросы, которые выполняются дольше порога.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.queries = []

    def __call__(self, request):
        start_time = time.time()
        
        # Включаем отслеживание запросов (только если DEBUG=True или в development)
        from django.conf import settings
        from django.db import connection
        
        # Сохраняем исходное состояние
        old_debug = getattr(connection, 'queries_logged', False)
        
        # Включаем логирование запросов для мониторинга
        if settings.DEBUG or env("DJANGO_ENV") == "development":
            connection.queries_logged = True

        response = self.get_response(request)
        
        # Восстанавливаем состояние
        connection.queries_logged = old_debug
        
        total_time = time.time() - start_time
        query_count = len(connection.queries) if hasattr(connection, 'queries') else 0
        
        if query_count > 0:
            total_query_time = sum(float(q['time']) for q in connection.queries)
            
            # Логируем медленные запросы
            for query in connection.queries:
                query_time = float(query.get('time', 0))
                if query_time > SLOW_QUERY_THRESHOLD:
                    logger.warning(
                        f'Медленный SQL запрос ({query_time:.3f} сек): {query.get("sql", "")[:200]}',
                        extra={
                            'query_time': query_time,
                            'sql': query.get('sql', '')[:500],
                            'path': request.path,
                        }
                    )
            
            # Логируем общую статистику для медленных запросов
            if total_query_time > SLOW_QUERY_THRESHOLD:
                logger.info(
                    f'Запрос {request.path}: {query_count} SQL запросов, '
                    f'общее время: {total_query_time:.3f} сек, '
                    f'время обработки: {total_time:.3f} сек'
                )

        return response


def check_database_connections():
    """
    Проверка количества активных соединений к БД.
    
    Returns:
        Словарь с информацией о соединениях
    """
    try:
        with connection.cursor() as cursor:
            # Получаем информацию о соединениях (PostgreSQL)
            cursor.execute("""
                SELECT 
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active_connections,
                    count(*) FILTER (WHERE state = 'idle') as idle_connections,
                    setting::int as max_connections
                FROM pg_stat_activity, pg_settings
                WHERE name = 'max_connections'
                GROUP BY max_connections
            """)
            
            row = cursor.fetchone()
            if row:
                total, active, idle, max_conn = row
                usage_percent = (total / max_conn) * 100 if max_conn > 0 else 0
                
                result = {
                    'total_connections': total,
                    'active_connections': active,
                    'idle_connections': idle,
                    'max_connections': max_conn,
                    'usage_percent': usage_percent,
                }
                
                # Логируем предупреждения
                if usage_percent >= MAX_CONNECTIONS_CRITICAL:
                    logger.critical(
                        f'КРИТИЧЕСКИЙ уровень использования соединений: '
                        f'{usage_percent:.1f}% ({total}/{max_conn})'
                    )
                elif usage_percent >= MAX_CONNECTIONS_WARNING:
                    logger.warning(
                        f'Высокий уровень использования соединений: '
                        f'{usage_percent:.1f}% ({total}/{max_conn})'
                    )
                
                return result
    except Exception as e:
        logger.error(f'Ошибка при проверке соединений: {e}')
        return None


@receiver(request_started)
def log_request_start(sender, **kwargs):
    """Логирование начала запроса для мониторинга."""
    pass


@receiver(request_finished)
def log_request_finish(sender, **kwargs):
    """Логирование окончания запроса и проверка соединений."""
    # Периодически проверяем соединения (каждый 100-й запрос)
    import random
    if random.random() < 0.01:  # 1% запросов
        check_database_connections()
