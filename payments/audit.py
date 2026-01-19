import logging
from typing import Optional, Dict, Any

from django.db import models
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.utils import timezone

User = get_user_model()
logger = logging.getLogger(__name__)


class AuditLog(models.Model):
    """
    Model for audit of all operations with payout requests.
    """
    
    class Action(models.TextChoices):
        CREATE = 'create', 'Создание'
        UPDATE = 'update', 'Обновление'
        DELETE = 'delete', 'Удаление'
        STATUS_CHANGE = 'status_change', 'Изменение статуса'
        VIEW = 'view', 'Просмотр'
    
    action = models.CharField(max_length=20, choices=Action.choices)
    payout_id = models.UUIDField(db_index=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = 'Аудит лог'
        verbose_name_plural = 'Аудит логи'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['payout_id', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]
    
    def __str__(self):
        return f'{self.get_action_display()} заявки {self.payout_id} в {self.timestamp}'


class AuditService:
    """Service for recording audit."""
    
    @staticmethod
    def log_action(
        action: str,
        payout_id: str,
        user: Optional[Any] = None,
        request: Optional[HttpRequest] = None,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Recording action in audit log.
        
        Args:
            action: Тип действия (create, update, delete, etc.)
            payout_id: UUID заявки
            user: Пользователь, выполнивший действие
            request: HTTP request (для IP и user agent)
            old_value: Старое значение (для update)
            new_value: Новое значение (для update)
            metadata: Дополнительные метаданные
        """
        try:
            ip_address = None
            user_agent = ''
            
            if request:
                ip_address = AuditService._get_client_ip(request)
                user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            AuditLog.objects.create(
                action=action,
                payout_id=payout_id,
                user=user if user and user.is_authenticated else None,
                ip_address=ip_address,
                user_agent=user_agent,
                old_value=old_value,
                new_value=new_value,
                metadata=metadata or {}
            )
        except Exception as e:
            logger.error(f'Ошибка записи аудита: {e}')
    
    @staticmethod
    def _get_client_ip(request: HttpRequest) -> Optional[str]:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
