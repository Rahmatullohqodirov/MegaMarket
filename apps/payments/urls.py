from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PromoCodeViewSet,
    PaymentViewSet,
    SellerBalanceViewSet,
    WithdrawalRequestViewSet
)

router = DefaultRouter()
router.register(r'promo-codes', PromoCodeViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'balance', SellerBalanceViewSet)
router.register(r'withdrawals', WithdrawalRequestViewSet)

urlpatterns = [
    path('', include(router.urls)),
]