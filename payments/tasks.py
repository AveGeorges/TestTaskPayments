import logging

from celery import shared_task

from .services import PayoutService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def process_payout_async(self, external_id: str) -> dict:
    logger.info(f'[Celery] Запуск обработки заявки {external_id}')
    
    try:
        payout = PayoutService.start_processing(external_id)
        
        if payout is None:
            return {'status': 'skipped', 'reason': 'already_processed'}
        
        logger.info(f'[Celery] Валидация реквизитов...')
        is_valid = PayoutService.validate_recipient(payout.recipient_details)
        
        if not is_valid:
            result = PayoutService.fail_payout(
                external_id, 
                'Невалидные реквизиты получателя'
            )
            return {
                'status': result.status,
                'message': result.message
            }
        
        logger.info(f'[Celery] Запрос к платёжному шлюзу...')
        success, message = PayoutService.process_payment_gateway(
            payout.amount,
            payout.currency,
            payout.recipient_details
        )
        
        if success:
            result = PayoutService.complete_payout(external_id)
        else:
            result = PayoutService.fail_payout(external_id, message)
        
        logger.info(f'[Celery] Завершено: {result.status}')
        
        return {
            'status': result.status,
            'external_id': result.external_id,
            'message': result.message,
            'success': result.success
        }
        
    except Exception as exc:
        logger.error(f'[Celery] Критическая ошибка: {exc}')
        
        PayoutService.fail_payout(external_id, str(exc))
        
        if self.request.retries < self.max_retries:
            countdown = self.default_retry_delay * (2 ** self.request.retries)
            logger.info(f'[Celery] Повторная попытка через {countdown}с...')
            raise self.retry(exc=exc, countdown=countdown)
        
        return {'status': 'failed', 'error': str(exc)}
