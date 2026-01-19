import logging

from decimal import Decimal
from typing import Optional
from dataclasses import dataclass

from django.db import transaction

from .models import PayoutRequest
from .repository import PayoutRepository
from .constants import (
    MIN_CARD_NUMBER_LENGTH,
    MIN_ACCOUNT_LENGTH,
    MIN_WALLET_ID_LENGTH,
    RECIPIENT_TYPES,
)

logger = logging.getLogger(__name__)


@dataclass
class PayoutResult:
    """Result for payout operation"""
    success: bool
    external_id: str
    status: str
    message: str


class PayoutService:
    """Service for payout operations"""
    @staticmethod
    @transaction.atomic
    def start_processing(external_id: str) -> Optional[PayoutRequest]:
        payout = PayoutRepository.get_by_external_id_for_update(external_id)
        
        if not payout:
            logger.error(f'Заявка {external_id} не найдена')
            return None
        
        if payout.status != PayoutRequest.Status.PENDING:
            logger.warning(
                f'Заявка {external_id} уже обработана, статус: {payout.status}'
            )
            return None
        
        PayoutRepository.update_status(payout, PayoutRequest.Status.PROCESSING)
        logger.info(f'Заявка {external_id}: статус → processing')
        return payout
    
    @staticmethod
    @transaction.atomic
    def complete_payout(external_id: str) -> PayoutResult:
        payout = PayoutRepository.get_by_external_id_for_update(external_id)
        
        if not payout:
            return PayoutResult(
                success=False,
                external_id=str(external_id),
                status='error',
                message='Заявка не найдена'
            )
        
        PayoutRepository.update_status(payout, PayoutRequest.Status.COMPLETED)
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
        payout = PayoutRepository.get_by_external_id_for_update(external_id)
        
        if not payout:
            return PayoutResult(
                success=False,
                external_id=str(external_id),
                status='error',
                message='Заявка не найдена'
            )
        
        PayoutRepository.update_status(payout, PayoutRequest.Status.FAILED)
        logger.warning(f'Заявка {external_id}: ошибка — {reason}')
        
        return PayoutResult(
            success=False,
            external_id=str(external_id),
            status=payout.status,
            message=reason or 'Ошибка обработки выплаты'
        )
    
    @staticmethod
    def validate_recipient(recipient_details: dict) -> bool:
        import time
        
        time.sleep(0.5)
        
        recipient_type = recipient_details.get('type')
        
        if recipient_type == 'card':
            number = recipient_details.get('number', '')
            return len(str(number)) >= MIN_CARD_NUMBER_LENGTH
        
        elif recipient_type == 'account':
            account = recipient_details.get('account', '')
            return len(str(account)) >= MIN_ACCOUNT_LENGTH
        
        elif recipient_type == 'wallet':
            wallet_id = recipient_details.get('wallet_id', '')
            return len(str(wallet_id)) >= MIN_WALLET_ID_LENGTH
        
        return False
    
    @staticmethod
    def process_payment_gateway(
        amount: Decimal,
        currency: str,
        recipient_details: dict
    ) -> tuple[bool, str]:
        import time
        import random
        
        time.sleep(random.uniform(1, 3))
        
        if random.random() < 0.1:
            return False, 'Платёжный шлюз вернул ошибку: недостаточно средств'
        
        logger.info(
            f'Платёжный шлюз: перевод {amount} {currency} на '
            f'{recipient_details.get("type")} выполнен'
        )
        return True, 'Платёж успешно проведён'
