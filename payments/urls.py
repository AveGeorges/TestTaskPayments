from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import PayoutRequestViewSet, health_check

router = DefaultRouter()
router.register(r'payouts', PayoutRequestViewSet, basename='payout')

urlpatterns = [
    path('health/', health_check, name='health-check'),
    path('', include(router.urls)),
]

