import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import PayoutRequest

logger = logging.getLogger(__name__)


@receiver(post_save, sender=PayoutRequest)
def on_payout_created(sender, instance: PayoutRequest, created: bool, **kwargs):
    """Запуск Celery задачи при создании заявки."""
    if not created:
        return
    
    external_id = str(instance.external_id)
    
    logger.info(
        f'[Signal] Заявка {external_id} создана, '
        f'запуск асинхронной обработки...'
    )
    
    def send_task():
        from .tasks import process_payout_async
        process_payout_async.delay(external_id)
    
    transaction.on_commit(send_task)

