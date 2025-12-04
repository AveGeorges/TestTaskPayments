import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import PayoutRequest

logger = logging.getLogger(__name__)


@receiver(post_save, sender=PayoutRequest)
def on_payout_created(sender, instance: PayoutRequest, created: bool, **kwargs):
    """Запуск Celery задачи при создании заявки."""
    if not created:
        return
    
    from .tasks import process_payout_async
    
    logger.info(
        f'[Signal] Заявка {instance.external_id} создана, '
        f'запуск асинхронной обработки...'
    )
    
    process_payout_async.delay(str(instance.external_id))

