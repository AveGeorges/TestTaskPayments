from rest_framework import serializers

from .models import PayoutRequest
from .constants import (
    MAX_PAYOUT_AMOUNT,
    MIN_PAYOUT_AMOUNT,
    RECIPIENT_TYPES,
    MIN_CARD_NUMBER_LENGTH,
    MIN_ACCOUNT_LENGTH,
    MIN_WALLET_ID_LENGTH,
)
from .exceptions import (
    PayoutAmountLimitError,
    PayoutValidationError,
)


class PayoutRequestSerializer(serializers.ModelSerializer):
    """Serializer for payout request"""
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    currency_display = serializers.CharField(
        source='get_currency_display',
        read_only=True
    )

    class Meta:
        model = PayoutRequest
        fields = [
            'external_id',
            'amount',
            'currency',
            'currency_display',
            'recipient_details',
            'status',
            'status_display',
            'description',
            'idempotency_key',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'external_id', 'created_at', 'updated_at']

    def validate_amount(self, value):
        if value < MIN_PAYOUT_AMOUNT:
            raise serializers.ValidationError(
                f'Сумма должна быть не менее {MIN_PAYOUT_AMOUNT}.'
            )
        if value > MAX_PAYOUT_AMOUNT:
            raise serializers.ValidationError(
                f'Сумма не может превышать {MAX_PAYOUT_AMOUNT}.'
            )
        return value

    def validate_recipient_details(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError('Реквизиты должны быть объектом JSON.')
        
        required_fields = ['type']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f'Поле "{field}" обязательно в реквизитах.')
        
        recipient_type = value.get('type')
        if recipient_type not in RECIPIENT_TYPES:
            raise serializers.ValidationError(
                f'Тип реквизитов должен быть одним из: {", ".join(RECIPIENT_TYPES)}.'
            )
        
        if recipient_type == 'card':
            number = value.get('number', '')
            if not number or len(str(number)) < MIN_CARD_NUMBER_LENGTH:
                raise serializers.ValidationError(
                    f'Номер карты должен содержать не менее {MIN_CARD_NUMBER_LENGTH} символов.'
                )
        elif recipient_type == 'account':
            account = value.get('account', '')
            if not account or len(str(account)) < MIN_ACCOUNT_LENGTH:
                raise serializers.ValidationError(
                    f'Номер счёта должен содержать не менее {MIN_ACCOUNT_LENGTH} символов.'
                )
        elif recipient_type == 'wallet':
            wallet_id = value.get('wallet_id', '')
            if not wallet_id or len(str(wallet_id)) < MIN_WALLET_ID_LENGTH:
                raise serializers.ValidationError(
                    f'ID кошелька должен содержать не менее {MIN_WALLET_ID_LENGTH} символов.'
                )
        
        return value

    def validate_status(self, value):
        if self.instance and self.instance.is_final_status:
            raise serializers.ValidationError(
                'Нельзя изменить статус заявки, находящейся в финальном состоянии.'
            )
        return value


class PayoutRequestCreateSerializer(PayoutRequestSerializer):
    """Serializer for creating payout request"""
    idempotency_key = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=True,
        help_text='Уникальный ключ для предотвращения дублирования заявок'
    )
    
    class Meta(PayoutRequestSerializer.Meta):
        fields = PayoutRequestSerializer.Meta.fields + ['idempotency_key']
        read_only_fields = ['id', 'external_id', 'status', 'created_at', 'updated_at']


class PayoutRequestUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating payout request"""
    class Meta:
        model = PayoutRequest
        fields = ['status', 'description']

    def validate_status(self, value):
        if self.instance and self.instance.is_final_status:
            raise serializers.ValidationError(
                'Нельзя изменить статус заявки, находящейся в финальном состоянии.'
            )
        
        if self.instance:
            current = self.instance.status
            allowed_transitions = {
                PayoutRequest.Status.PENDING: [
                    PayoutRequest.Status.PROCESSING,
                    PayoutRequest.Status.CANCELLED
                ],
                PayoutRequest.Status.PROCESSING: [
                    PayoutRequest.Status.COMPLETED,
                    PayoutRequest.Status.FAILED,
                    PayoutRequest.Status.CANCELLED
                ],
            }
            
            if current in allowed_transitions and value not in allowed_transitions[current]:
                allowed = [s.value for s in allowed_transitions.get(current, [])]
                raise serializers.ValidationError(
                    f'Недопустимый переход статуса. Из "{current}" можно перейти в: {", ".join(allowed)}.'
                )
        
        return value

