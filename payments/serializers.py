from rest_framework import serializers

from .models import PayoutRequest


class PayoutRequestSerializer(serializers.ModelSerializer):
    """
    Сериализатор для заявки на выплату.
    """
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
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'external_id', 'created_at', 'updated_at']

    def validate_amount(self, value):
        """Валидация суммы выплаты."""
        if value <= 0:
            raise serializers.ValidationError('Сумма должна быть положительной.')
        return value

    def validate_recipient_details(self, value):
        """Валидация реквизитов получателя."""
        if not isinstance(value, dict):
            raise serializers.ValidationError('Реквизиты должны быть объектом JSON.')
        
        required_fields = ['type']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f'Поле "{field}" обязательно в реквизитах.')
        
        valid_types = ['card', 'account', 'wallet']
        if value.get('type') not in valid_types:
            raise serializers.ValidationError(
                f'Тип реквизитов должен быть одним из: {", ".join(valid_types)}.'
            )
        
        return value

    def validate_status(self, value):
        """Валидация статуса при обновлении."""
        if self.instance and self.instance.is_final_status:
            raise serializers.ValidationError(
                'Нельзя изменить статус заявки, находящейся в финальном состоянии.'
            )
        return value


class PayoutRequestCreateSerializer(PayoutRequestSerializer):
    """
    Сериализатор для создания заявки (статус устанавливается автоматически).
    """
    class Meta(PayoutRequestSerializer.Meta):
        read_only_fields = ['id', 'external_id', 'status', 'created_at', 'updated_at']


class PayoutRequestUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для обновления заявки (только статус и описание).
    """
    class Meta:
        model = PayoutRequest
        fields = ['status', 'description']

    def validate_status(self, value):
        """Валидация перехода статуса."""
        if self.instance and self.instance.is_final_status:
            raise serializers.ValidationError(
                'Нельзя изменить статус заявки, находящейся в финальном состоянии.'
            )
        
        # Валидация допустимых переходов статусов
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

