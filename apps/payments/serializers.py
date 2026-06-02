from django.contrib.auth import forms
from rest_framework import serializers
from .models import PromoCode, Payment, SellerBalance, WithdrawalRequest


class PromoCodeSerializer(serializers.ModelSerializer):
    is_valid = serializers.ReadOnlyField()
    class Meta:
        model = PromoCode
        fields = '__all__'


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'


class SellerBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerBalance
        fields = '__all__'


class WithdrawalRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = WithdrawalRequest
        fields = '__all__'