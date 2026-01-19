from typing import Any

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from django.db import sync_to_async
from django.core.cache import cache
from django.http import HttpRequest

from .repository import PayoutRepository
from .serializers import PayoutRequestSerializer


@api_view(['GET'])
async def async_list_payouts(request: HttpRequest) -> Response:
    """
    Async view for getting list of payout requests.
    """
    from rest_framework.permissions import IsAdminUser
    
    if not IsAdminUser().has_permission(request, None):
        return Response(
            {'detail': 'You do not have permission to perform this action.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    cache_key = f'payouts_list:{request.GET.urlencode()}'
    
    cached_data = await sync_to_async(cache.get)(cache_key)
    if cached_data:
        return Response(cached_data)
    
    queryset = await sync_to_async(list)(
        PayoutRepository.get_all()[:100]  # Ограничение для безопасности
    )
    serializer = PayoutRequestSerializer(queryset, many=True)
    data = serializer.data
    
    await sync_to_async(cache.set)(cache_key, data, 60)  # Кэш на 60 сек
    
    return Response(data)


@api_view(['GET'])
async def async_get_payout(request: HttpRequest, external_id: str) -> Response:
    """
    Async view for getting one payout request.
    """
    from rest_framework.permissions import IsAdminUser
    
    if not IsAdminUser().has_permission(request, None):
        return Response(
            {'detail': 'You do not have permission to perform this action.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    cache_key = f'payout:{external_id}'
    
    cached_data = await sync_to_async(cache.get)(cache_key)
    if cached_data:
        return Response(cached_data)
    
    payout = await sync_to_async(PayoutRepository.get_by_external_id)(external_id)
    
    if not payout:
        return Response(
            {'detail': 'Заявка не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = PayoutRequestSerializer(payout)
    data = serializer.data
    
    await sync_to_async(cache.set)(cache_key, data, 300)  # Кэш на 5 минут
    
    return Response(data)
