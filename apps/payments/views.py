from rest_framework import viewsets
from .models import PromoCode, Payment, SellerBalance, WithdrawalRequest
from apps.payments.serializers import (
    PromoCodeSerializer,
    PaymentSerializer,
    SellerBalanceSerializer,
    WithdrawalRequestSerializer
)


class PromoCodeViewSet(viewsets.ModelViewSet):
    queryset = PromoCode.objects.all()
    serializer_class = PromoCodeSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer


class SellerBalanceViewSet(viewsets.ModelViewSet):
    queryset = SellerBalance.objects.all()
    serializer_class = SellerBalanceSerializer


class WithdrawalRequestViewSet(viewsets.ModelViewSet):
    queryset = WithdrawalRequest.objects.all()
    serializer_class = WithdrawalRequestSerializer