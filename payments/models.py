import uuid
from decimal import Decimal

from django.db import models
from django.core.validators import MinValueValidator


class PayoutRequest(models.Model):
    """
    Модель заявки на выплату средств.
    """

    class Status(models.TextChoices):
        """Статусы заявки на выплату."""
        PENDING = 'pending', 'Ожидает обработки'
        PROCESSING = 'processing', 'В обработке'
        COMPLETED = 'completed', 'Выполнена'
        FAILED = 'failed', 'Ошибка'
        CANCELLED = 'cancelled', 'Отменена'

    class Currency(models.TextChoices):
        """Поддерживаемые валюты."""
        RUB = 'RUB', 'Российский рубль'
        USD = 'USD', 'Доллар США'
        EUR = 'EUR', 'Евро'
        YEN = 'YEN', 'Японский иен'
        GBP = 'GBP', 'Британский фунт стерлингов'
        AUD = 'AUD', 'Австралийский доллар'
        CNY = 'CNY', 'Китайский юань'
        KZT = 'KZT', 'Казахстанский тенге'
        BYN = 'BYN', 'Белорусский рубль'
        AED = 'AED', 'Дирхам ОАЭ'

    external_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name='Внешний идентификатор',
        help_text='UUID для идентификатора заявки во внешних системах'
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Сумма выплаты',
        help_text='Сумма в указанной валюте (минимум 0.01)'
    )

    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.RUB,
        verbose_name='Валюта'
    )

    recipient_details = models.JSONField(
        verbose_name='Реквизиты получателя',
        help_text='JSON с реквизитами: тип (card/account/wallet), номер, ФИО и др.'
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name='Статус'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    description = models.TextField(
        blank=True,
        default='',
        verbose_name='Описание',
        help_text='Опциональный комментарий к заявке'
    )

    class Meta:
        verbose_name = 'Заявка на выплату'
        verbose_name_plural = 'Заявки на выплату'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['currency']),
        ]

    def __str__(self):
        return f'Заявка #{self.pk} - {self.amount} {self.currency} ({self.get_status_display()})'

    @property
    def is_final_status(self) -> bool:
        """Проверяет, находится ли заявка в финальном статусе."""
        return self.status in (self.Status.COMPLETED, self.Status.FAILED, self.Status.CANCELLED)
