from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import PayoutRequest
from .serializers import (
    PayoutRequestSerializer,
    PayoutRequestCreateSerializer,
    PayoutRequestUpdateSerializer,
)


@extend_schema_view(
    list=extend_schema(
        summary='Список заявок на выплату',
        description='Получение списка всех заявок с возможностью фильтрации и сортировки.',
        tags=['Платежи'],
        operation_id='1_payouts_list',
    ),
    retrieve=extend_schema(
        summary='Получение заявки',
        description='Получение детальной информации о заявке по внешнему идентификатору uuid.',
        tags=['Платежи'],
        operation_id='2_payouts_retrieve',
    ),
    create=extend_schema(
        summary='Создание заявки',
        description='Создание новой заявки на выплату.',
        tags=['Платежи'],
        operation_id='3_payouts_create',
    ),
    partial_update=extend_schema(
        summary='Обновление заявки',
        description='Частичное обновление заявки (изменение статуса или описания) по внешнему идентификатору uuid.',
        tags=['Платежи'],
        operation_id='4_payouts_partial_update',
    ),
    destroy=extend_schema(
        summary='Удаление заявки',
        description='Удаление заявки на выплату по внешнему идентификатору uuid.',
        tags=['Платежи'],
        operation_id='5_payouts_destroy',
    ),
)
class PayoutRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления заявками на выплату.
    
    Поддерживает все CRUD-операции:
    - GET /api/payouts/ — список заявок
    - GET /api/payouts/{external_id}/ — получение заявки
    - POST /api/payouts/ — создание заявки
    - PATCH /api/payouts/{external_id}/ — обновление заявки
    - DELETE /api/payouts/{external_id}/ — удаление заявки
    """
    queryset = PayoutRequest.objects.all()
    lookup_field = 'external_id'
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'currency']
    ordering_fields = ['created_at', 'updated_at', 'amount']
    ordering = ['-created_at']
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия."""
        if self.action == 'create':
            return PayoutRequestCreateSerializer
        elif self.action == 'partial_update':
            return PayoutRequestUpdateSerializer
        return PayoutRequestSerializer

    def get_object_for_update(self):
        """Получение объекта с блокировкой для обновления (защита от race condition)."""
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = PayoutRequest.objects.select_for_update().get(**filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        """Обновление заявки с блокировкой записи."""
        instance = self.get_object_for_update()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Возвращаем полные данные через основной сериализатор
        output_serializer = PayoutRequestSerializer(instance)
        return Response(output_serializer.data)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """Удаление заявки с блокировкой и проверкой статуса."""
        instance = self.get_object_for_update()
        
        if instance.status == PayoutRequest.Status.PROCESSING:
            return Response(
                {'detail': 'Нельзя удалить заявку, находящуюся в обработке.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
