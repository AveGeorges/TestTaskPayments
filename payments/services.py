import logging

from decimal import Decimal
from typing import Optional
from dataclasses import dataclass

from django.db import transaction

from .models import PayoutRequest

logger = logging.getLogger(__name__)


@dataclass
class PayoutResult:
    success: bool
    external_id: str
    status: str
    message: str


class PayoutService:
    """Сервис для обработки заявок на выплату (используется в Celery tasks)."""
    
    @staticmethod
    @transaction.atomic
    def start_processing(external_id: str) -> Optional[PayoutRequest]:
        """
        Начало обработки заявки (pending → processing).
        
        Args:
            external_id: UUID заявки
            
        Returns:
            PayoutRequest или None если заявка уже обработана
        """
        try:
            payout = PayoutRequest.objects.select_for_update().get(
                external_id=external_id
            )
        except PayoutRequest.DoesNotExist:
            logger.error(f'Заявка {external_id} не найдена')
            return None
        
        if payout.status != PayoutRequest.Status.PENDING:
            logger.warning(
                f'Заявка {external_id} уже обработана, статус: {payout.status}'
            )
            return None
        
        payout.status = PayoutRequest.Status.PROCESSING
        payout.save(update_fields=['status', 'updated_at'])
        logger.info(f'Заявка {external_id}: статус → processing')
        return payout
    
    @staticmethod
    @transaction.atomic
    def complete_payout(external_id: str) -> PayoutResult:
        """
        Успешное завершение обработки (processing → completed).
        
        Args:
            external_id: UUID заявки
            
        Returns:
            PayoutResult с результатом операции
        """
        try:
            payout = PayoutRequest.objects.select_for_update().get(
                external_id=external_id
            )
        except PayoutRequest.DoesNotExist:
            return PayoutResult(
                success=False,
                external_id=str(external_id),
                status='error',
                message='Заявка не найдена'
            )
        
        payout.status = PayoutRequest.Status.COMPLETED
        payout.save(update_fields=['status', 'updated_at'])
        logger.info(f'Заявка {external_id}: успешно завершена ✓')
        
        return PayoutResult(
            success=True,
            external_id=str(external_id),
            status=payout.status,
            message='Выплата выполнена успешно'
        )
    
    @staticmethod
    @transaction.atomic
    def fail_payout(external_id: str, reason: str = '') -> PayoutResult:
        """
        Неуспешное завершение обработки (processing → failed).
        
        Args:
            external_id: UUID заявки
            reason: Причина ошибки
            
        Returns:
            PayoutResult с результатом операции
        """
        try:
            payout = PayoutRequest.objects.select_for_update().get(
                external_id=external_id
            )
        except PayoutRequest.DoesNotExist:
            return PayoutResult(
                success=False,
                external_id=str(external_id),
                status='error',
                message='Заявка не найдена'
            )
        
        payout.status = PayoutRequest.Status.FAILED
        payout.save(update_fields=['status', 'updated_at'])
        logger.warning(f'Заявка {external_id}: ошибка — {reason}')
        
        return PayoutResult(
            success=False,
            external_id=str(external_id),
            status=payout.status,
            message=reason or 'Ошибка обработки выплаты'
        )
    
    @staticmethod
    async def validate_recipient(recipient_details: dict) -> bool:
        """
        Асинхронная валидация реквизитов получателя.
        
        В реальности здесь был бы запрос к внешнему API.
        
        Args:
            recipient_details: Реквизиты для проверки
            
        Returns:
            True если реквизиты валидны
        """
        import asyncio
        
        await asyncio.sleep(0.5)
        
        recipient_type = recipient_details.get('type')
        
        if recipient_type == 'card':
            number = recipient_details.get('number', '')
            return len(number) >= 13
        
        elif recipient_type == 'account':
            account = recipient_details.get('account', '')
            return len(account) >= 10
        
        elif recipient_type == 'wallet':
            wallet_id = recipient_details.get('wallet_id', '')
            return len(wallet_id) >= 5
        
        return False
    
    @staticmethod
    async def process_payment_gateway(
        amount: Decimal,
        currency: str,
        recipient_details: dict
    ) -> tuple[bool, str]:
        """
        Асинхронный запрос к платёжному шлюзу.
        
        В реальности здесь был бы HTTP запрос к API банка/платёжной системы.
        
        Args:
            amount: Сумма
            currency: Валюта
            recipient_details: Реквизиты
            
        Returns:
            (success, message)
        """
        import asyncio
        import random
        
        await asyncio.sleep(random.uniform(1, 3))
        
        if random.random() < 0.1:
            return False, 'Платёжный шлюз вернул ошибку: недостаточно средств'
        
        logger.info(
            f'Платёжный шлюз: перевод {amount} {currency} на '
            f'{recipient_details.get("type")} выполнен'
        )
        return True, 'Платёж успешно проведён'
