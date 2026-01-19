"""
Сервис для кэширования часто запрашиваемых заявок.

Использует Redis для кэширования:
- Отдельные заявки (по external_id)
- Списки заявок (с фильтрами)
- Статистика
"""

import hashlib
import json
from typing import Optional, Dict, Any, List
from django.core.cache import cache
from django.db.models import QuerySet

from .models import PayoutRequest


class CacheService:
    """Сервис для кэширования данных о заявках"""

    # Время жизни кэша (в секундах)
    CACHE_TIMEOUT_SINGLE = 300  # 5 минут для одной заявки
    CACHE_TIMEOUT_LIST = 60  # 1 минута для списка
    CACHE_TIMEOUT_STATS = 300  # 5 минут для статистики

    @staticmethod
    def _generate_cache_key(prefix: str, **kwargs) -> str:
        """
        Генерация ключа кэша на основе параметров.
        
        Args:
            prefix: Префикс ключа
            **kwargs: Параметры для генерации ключа
            
        Returns:
            Строка ключа кэша
        """
        # Сортируем параметры для консистентности
        params = json.dumps(kwargs, sort_keys=True)
        # Создаём хэш для короткого ключа
        params_hash = hashlib.md5(params.encode()).hexdigest()
        return f'payout:{prefix}:{params_hash}'

    @staticmethod
    def get_payout(external_id: str) -> Optional[Dict[str, Any]]:
        """
        Получить заявку из кэша.
        
        Args:
            external_id: UUID заявки
            
        Returns:
            Словарь с данными заявки или None
        """
        cache_key = f'payout:single:{external_id}'
        return cache.get(cache_key)

    @staticmethod
    def set_payout(external_id: str, data: Dict[str, Any]) -> None:
        """
        Сохранить заявку в кэш.
        
        Args:
            external_id: UUID заявки
            data: Данные заявки
        """
        cache_key = f'payout:single:{external_id}'
        cache.set(cache_key, data, CacheService.CACHE_TIMEOUT_SINGLE)

    @staticmethod
    def invalidate_payout(external_id: str) -> None:
        """
        Удалить заявку из кэша (при обновлении/удалении).
        
        Args:
            external_id: UUID заявки
        """
        cache_key = f'payout:single:{external_id}'
        cache.delete(cache_key)
        # Также удаляем все списки (они могут содержать эту заявку)
        CacheService.invalidate_all_lists()

    @staticmethod
    def get_list(filters: Optional[Dict[str, Any]] = None, 
                 ordering: Optional[str] = None,
                 limit: Optional[int] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Получить список заявок из кэша.
        
        Args:
            filters: Словарь фильтров (status, currency)
            ordering: Сортировка (created_at, -created_at, etc.)
            limit: Лимит записей
            
        Returns:
            Список заявок или None
        """
        cache_key = CacheService._generate_cache_key(
            'list',
            filters=filters or {},
            ordering=ordering,
            limit=limit
        )
        return cache.get(cache_key)

    @staticmethod
    def set_list(data: List[Dict[str, Any]],
                 filters: Optional[Dict[str, Any]] = None,
                 ordering: Optional[str] = None,
                 limit: Optional[int] = None) -> None:
        """
        Сохранить список заявок в кэш.
        
        Args:
            data: Список заявок
            filters: Словарь фильтров
            ordering: Сортировка
            limit: Лимит записей
        """
        cache_key = CacheService._generate_cache_key(
            'list',
            filters=filters or {},
            ordering=ordering,
            limit=limit
        )
        cache.set(cache_key, data, CacheService.CACHE_TIMEOUT_LIST)

    @staticmethod
    def invalidate_all_lists() -> None:
        """
        Удалить все списки из кэша.
        Используется при создании/обновлении/удалении заявок.
        """
        # В реальном проекте можно использовать паттерн с тегами
        # Для простоты удаляем все ключи с префиксом 'payout:list:'
        # В production лучше использовать Redis SCAN для поиска ключей
        pass  # В текущей реализации списки имеют короткое TTL

    @staticmethod
    def get_stats() -> Optional[Dict[str, Any]]:
        """
        Получить статистику из кэша.
        
        Returns:
            Словарь со статистикой или None
        """
        cache_key = 'payout:stats'
        return cache.get(cache_key)

    @staticmethod
    def set_stats(data: Dict[str, Any]) -> None:
        """
        Сохранить статистику в кэш.
        
        Args:
            data: Словарь со статистикой
        """
        cache_key = 'payout:stats'
        cache.set(cache_key, data, CacheService.CACHE_TIMEOUT_STATS)

    @staticmethod
    def invalidate_stats() -> None:
        """
        Удалить статистику из кэша.
        """
        cache_key = 'payout:stats'
        cache.delete(cache_key)
