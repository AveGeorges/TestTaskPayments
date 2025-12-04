import asyncio
import logging

from asgiref.sync import sync_to_async
from celery import shared_task

from .models import PayoutRequest
from .services import PayoutService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def process_payout_async(self, external_id: str) -> dict:
    """Асинхронная обработка заявки на выплату."""
    logger.info(f'[Celery] Запуск async обработки заявки {external_id}')
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                _process_payout_coroutine(external_id)
            )
        finally:
            loop.close()
        
        return result
        
    except Exception as exc:
        logger.error(f'[Celery] Критическая ошибка: {exc}')
        
        PayoutService.fail_payout(external_id, str(exc))
        
        if self.request.retries < self.max_retries:
            countdown = self.default_retry_delay * (2 ** self.request.retries)
            logger.info(f'[Celery] Повторная попытка через {countdown}с...')
            raise self.retry(exc=exc, countdown=countdown)
        
        return {'status': 'failed', 'error': str(exc)}


async def _process_payout_coroutine(external_id: str) -> dict:
    """
    Асинхронная корутина обработки выплаты.
    
    Args:
        external_id: UUID заявки
        
    Returns:
        dict с результатом
    """
    logger.info(f'[Async] Начало обработки {external_id}')
    
    payout = await sync_to_async(PayoutService.start_processing)(external_id)
    
    if payout is None:
        return {'status': 'skipped', 'reason': 'already_processed'}
    
    logger.info(f'[Async] Валидация реквизитов...')
    is_valid = await PayoutService.validate_recipient(payout.recipient_details)
    
    if not is_valid:
        result = await sync_to_async(PayoutService.fail_payout)(
            external_id, 
            'Невалидные реквизиты получателя'
        )
        return {
            'status': result.status,
            'message': result.message
        }
    
    logger.info(f'[Async] Запрос к платёжному шлюзу...')
    success, message = await PayoutService.process_payment_gateway(
        payout.amount,
        payout.currency,
        payout.recipient_details
    )
    
    if success:
        result = await sync_to_async(PayoutService.complete_payout)(external_id)
    else:
        result = await sync_to_async(PayoutService.fail_payout)(external_id, message)
    
    logger.info(f'[Async] Завершено: {result.status}')
    
    return {
        'status': result.status,
        'external_id': result.external_id,
        'message': result.message,
        'success': result.success
    }
