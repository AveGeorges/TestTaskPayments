from typing import Optional, List
from django.db import transaction
from django.db.models import QuerySet

from .models import PayoutRequest


class PayoutRepository:
    """Repository for encapsulating database operations for payout requests"""

    @staticmethod
    def get_by_external_id(external_id: str) -> Optional[PayoutRequest]:
        """
        Получить заявку по external_id.
        Оптимизация: загружаем только нужные поля для чтения.
        """
        try:
            return PayoutRequest.objects.only(
                'external_id', 'amount', 'currency', 'recipient_details',
                'status', 'created_at', 'updated_at', 'description'
            ).get(external_id=external_id)
        except PayoutRequest.DoesNotExist:
            return None

    @staticmethod
    def get_by_external_id_for_update(external_id: str) -> Optional[PayoutRequest]:
        """
        Получить заявку по external_id с блокировкой для обновления.
        Оптимизация: загружаем все поля (нужны для обновления).
        """
        try:
            return PayoutRequest.objects.select_for_update().get(external_id=external_id)
        except PayoutRequest.DoesNotExist:
            return None

    @staticmethod
    def get_by_idempotency_key(idempotency_key: str) -> Optional[PayoutRequest]:
        """
        Получить заявку по idempotency_key.
        Оптимизация: загружаем только нужные поля.
        """
        try:
            return PayoutRequest.objects.only(
                'external_id', 'amount', 'currency', 'status', 'created_at'
            ).get(idempotency_key=idempotency_key)
        except PayoutRequest.DoesNotExist:
            return None

    @staticmethod
    def get_all() -> QuerySet[PayoutRequest]:
        """
        Получить все заявки.
        Оптимизация: загружаем только нужные поля для списка.
        """
        return PayoutRequest.objects.only(
            'external_id', 'amount', 'currency', 'status',
            'created_at', 'updated_at', 'description'
        ).all()

    @staticmethod
    def filter_by_status(status: str) -> QuerySet[PayoutRequest]:
        """
        Фильтр по статусу.
        Оптимизация: используем индекс на status, загружаем только нужные поля.
        """
        return PayoutRequest.objects.filter(status=status).only(
            'external_id', 'amount', 'currency', 'status',
            'created_at', 'updated_at'
        )

    @staticmethod
    def filter_by_currency(currency: str) -> QuerySet[PayoutRequest]:
        """
        Фильтр по валюте.
        Оптимизация: используем индекс на currency, загружаем только нужные поля.
        """
        return PayoutRequest.objects.filter(currency=currency).only(
            'external_id', 'amount', 'currency', 'status',
            'created_at', 'updated_at'
        )

    @staticmethod
    @transaction.atomic
    def create(**kwargs) -> PayoutRequest:
        return PayoutRequest.objects.create(**kwargs)

    @staticmethod
    @transaction.atomic
    def update_status(payout: PayoutRequest, new_status: str) -> PayoutRequest:
        payout.status = new_status
        payout.save(update_fields=['status', 'updated_at'])
        return payout

    @staticmethod
    @transaction.atomic
    def update(payout: PayoutRequest, **kwargs) -> PayoutRequest:
        for key, value in kwargs.items():
            setattr(payout, key, value)
        payout.save()
        return payout

    @staticmethod
    @transaction.atomic
    def delete(payout: PayoutRequest) -> None:
        payout.delete()

    @staticmethod
    def exists_by_idempotency_key(idempotency_key: str) -> bool:
        return PayoutRequest.objects.filter(idempotency_key=idempotency_key).exists()
