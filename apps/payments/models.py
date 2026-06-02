from django.db import models
from apps.users.models import User, SellerProfile


class PromoCode(models.Model):
    code             = models.CharField(max_length=20, unique=True)
    discount_percent = models.PositiveIntegerField()
    max_uses         = models.PositiveIntegerField(default=100)
    used_count       = models.PositiveIntegerField(default=0)
    min_amount       = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active        = models.BooleanField(default=True)
    starts_at        = models.DateTimeField(blank=True, null=True)
    expires_at       = models.DateTimeField(blank=True, null=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} — {self.discount_percent}%"

    @property
    def is_valid(self):
        from django.utils import timezone
        now = timezone.now()
        if not self.is_active:
            return False
        if self.used_count >= self.max_uses:
            return False
        if self.expires_at and now > self.expires_at:
            return False
        return True


class Payment(models.Model):
    class Provider(models.TextChoices):
        PAYME = 'payme', 'Payme'
        CLICK = 'click', 'Click'
        CASH  = 'cash',  'Naqd'

    class Status(models.TextChoices):
        PENDING   = 'pending',   'Kutilmoqda'
        PAID      = 'paid',      'To\'langan'
        FAILED    = 'failed',    'Muvaffaqiyatsiz'
        REFUNDED  = 'refunded',  'Qaytarildi'

    order          = models.OneToOneField('orders.Order', on_delete=models.CASCADE, related_name='payment')
    provider       = models.CharField(max_length=10, choices=Provider.choices)
    status         = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    provider_data  = models.JSONField(default=dict)
    paid_at        = models.DateTimeField(blank=True, null=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order.order_number} — {self.provider} — {self.status}"


class SellerBalance(models.Model):
    class Type(models.TextChoices):
        CREDIT     = 'credit',     'Kirim'
        WITHDRAWAL = 'withdrawal', 'Chiqim'
        REFUND     = 'refund',     'Qaytarish'

    seller     = models.ForeignKey('users.SellerProfile', on_delete=models.CASCADE, related_name='balance_logs')
    order      = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    type       = models.CharField(max_length=12, choices=Type.choices)
    note       = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.seller.shop_name} — {self.type} — {self.amount}"


class WithdrawalRequest(models.Model):
    class Status(models.TextChoices):
        PENDING  = 'pending',  'Kutilmoqda'
        APPROVED = 'approved', 'Tasdiqlandi'
        REJECTED = 'rejected', 'Rad etildi'

    seller     = models.ForeignKey(SellerProfile, on_delete=models.CASCADE, related_name='withdrawals')
    amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    card_number = models.CharField(max_length=16)
    status     = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    note       = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)