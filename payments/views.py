import logging
from typing import Any

from django.db import transaction
from django.db import IntegrityError
from django.http import HttpRequest
from rest_framework import viewsets, status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from .models import PayoutRequest
from .repository import PayoutRepository
from .serializers import (
    PayoutRequestSerializer,
    PayoutRequestCreateSerializer,
    PayoutRequestUpdateSerializer,
)
from .exceptions import DuplicatePayoutError
from .audit import AuditService
from .cache_service import CacheService

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary='Список заявок на выплату',
        description='Получение списка всех заявок с возможностью фильтрации и сортировки.',
        tags=['Платежи'],
        operation_id='1_payouts_list',
        parameters=[
            OpenApiParameter(
                name='ordering',
                description='Сортировка. Доступные поля: created_at, updated_at, amount. '
                           'Для сортировки по убыванию добавьте "-" (например: -created_at)',
                required=False,
                type=str,
            ),
        ],
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
    """ViewSet for payout request"""
    queryset = PayoutRepository.get_all()
    lookup_field = 'external_id'
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'currency']
    ordering_fields = ['created_at', 'updated_at', 'amount']
    ordering = ['-created_at']
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_serializer_class(self) -> type:
        if self.action == 'create':
            return PayoutRequestCreateSerializer
        elif self.action == 'partial_update':
            return PayoutRequestUpdateSerializer
        return PayoutRequestSerializer

    def retrieve(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Response:
        """Получение одной заявки с кэшированием."""
        external_id = kwargs.get(self.lookup_field)
        
        # Пытаемся получить из кэша
        cached_data = CacheService.get_payout(str(external_id))
        if cached_data:
            return Response(cached_data)
        
        # Если нет в кэше, получаем из БД
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        
        # Сохраняем в кэш
        CacheService.set_payout(str(external_id), data)
        
        return Response(data)

    def list(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Response:
        """Список заявок с кэшированием."""
        # Получаем параметры фильтрации
        filters = {
            'status': request.query_params.get('status'),
            'currency': request.query_params.get('currency'),
        }
        filters = {k: v for k, v in filters.items() if v}  # Убираем None
        ordering = request.query_params.get('ordering', '-created_at')
        
        # Пытаемся получить из кэша
        cached_data = CacheService.get_list(filters=filters, ordering=ordering)
        if cached_data:
            return Response(cached_data)
        
        # Если нет в кэше, получаем из БД
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = self.get_paginated_response(serializer.data).data
        else:
            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data
        
        # Сохраняем в кэш (только первые 100 записей для экономии памяти)
        if isinstance(data, dict) and 'results' in data:
            CacheService.set_list(data['results'][:100], filters=filters, ordering=ordering)
        elif isinstance(data, list):
            CacheService.set_list(data[:100], filters=filters, ordering=ordering)
        
        return Response(data)

    @transaction.atomic
    def create(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        idempotency_key = serializer.validated_data.get('idempotency_key')
        
        # Проверка на дублирование по idempotency_key
        if idempotency_key:
            existing_payout = PayoutRepository.get_by_idempotency_key(idempotency_key)
            if existing_payout:
                logger.info(
                    f'Дублирование заявки предотвращено по idempotency_key: {idempotency_key}'
                )
                output_serializer = PayoutRequestSerializer(existing_payout)
                return Response(
                    output_serializer.data,
                    status=status.HTTP_200_OK
                )
        
        try:
            payout = serializer.save()
        except IntegrityError as e:
            # Обработка race condition: если заявка создалась между проверкой и сохранением
            if 'idempotency_key' in str(e).lower() or 'unique' in str(e).lower():
                if idempotency_key:
                    existing_payout = PayoutRepository.get_by_idempotency_key(idempotency_key)
                    if existing_payout:
                        logger.info(
                            f'Дублирование предотвращено (race condition) по idempotency_key: {idempotency_key}'
                        )
                        output_serializer = PayoutRequestSerializer(existing_payout)
                        return Response(
                            output_serializer.data,
                            status=status.HTTP_200_OK
                        )
            logger.error(f'Ошибка создания заявки: {e}')
            raise
        
        output_serializer = PayoutRequestSerializer(payout)
        
        # Сохраняем в кэш
        CacheService.set_payout(str(payout.external_id), output_serializer.data)
        # Инвалидируем списки
        CacheService.invalidate_all_lists()
        
        AuditService.log_action(
            action='create',
            payout_id=str(payout.external_id),
            user=request.user if hasattr(request, 'user') else None,
            request=request,
            new_value=output_serializer.data
        )
        
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def get_object_for_update(self) -> PayoutRequest:
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        external_id = self.kwargs[lookup_url_kwarg]
        obj = PayoutRepository.get_by_external_id_for_update(external_id)
        if not obj:
            from rest_framework.exceptions import NotFound
            raise NotFound(f'Заявка с external_id={external_id} не найдена')
        self.check_object_permissions(self.request, obj)
        return obj

    @transaction.atomic
    def partial_update(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Response:
        instance = self.get_object_for_update()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        old_data = PayoutRequestSerializer(instance).data
        self.perform_update(serializer)
        instance.refresh_from_db()
        new_data = PayoutRequestSerializer(instance).data
        
        # Обновляем кэш
        CacheService.set_payout(str(instance.external_id), new_data)
        # Инвалидируем списки
        CacheService.invalidate_all_lists()
        
        AuditService.log_action(
            action='update',
            payout_id=str(instance.external_id),
            user=request.user if hasattr(request, 'user') else None,
            request=request,
            old_value=old_data,
            new_value=new_data
        )
        
        output_serializer = PayoutRequestSerializer(instance)
        return Response(output_serializer.data)

    @transaction.atomic
    def destroy(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Response:
        instance = self.get_object_for_update()
        
        if instance.status == PayoutRequest.Status.PROCESSING:
            return Response(
                {'detail': 'Нельзя удалить заявку, находящуюся в обработке.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payout_id = str(instance.external_id)
        old_data = PayoutRequestSerializer(instance).data
        
        AuditService.log_action(
            action='delete',
            payout_id=payout_id,
            user=request.user if hasattr(request, 'user') else None,
            request=request,
            old_value=old_data
        )
        
        self.perform_destroy(instance)
        
        # Удаляем из кэша
        CacheService.invalidate_payout(payout_id)
        
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request: HttpRequest) -> Response:
    """Health check view"""
    from django.db import connection
    from django.core.cache import cache
    from celery import current_app
    
    health_status = {
        'status': 'healthy',
        'checks': {}
    }
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['checks']['database'] = 'ok'
    except Exception as e:
        health_status['checks']['database'] = f'error: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    try:
        cache.set('health_check', 'ok', 10)
        cache.get('health_check')
        health_status['checks']['cache'] = 'ok'
    except Exception as e:
        health_status['checks']['cache'] = f'error: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    try:
        inspect = current_app.control.inspect()
        stats = inspect.stats()
        if stats:
            health_status['checks']['celery'] = 'ok'
        else:
            health_status['checks']['celery'] = 'warning: no workers available'
    except Exception as e:
        health_status['checks']['celery'] = f'warning: {str(e)}'
    
    http_status = status.HTTP_200_OK if health_status['status'] == 'healthy' else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return Response(health_status, status=http_status)
