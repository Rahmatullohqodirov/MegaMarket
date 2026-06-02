from django.db import models
from apps.users.models import User


class Notification(models.Model):
    class Type(models.TextChoices):
        ORDER       = 'order',      'Buyurtma'
        PAYMENT     = 'payment',    'To\'lov'
        PRODUCT     = 'product',    'Mahsulot'
        SELLER      = 'seller',     'Sotuvchi'
        PROMO       = 'promo',      'Aksiya'
        SYSTEM      = 'system',     'Tizim'

    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type       = models.CharField(max_length=10, choices=Type.choices, default=Type.SYSTEM)
    title      = models.CharField(max_length=200)
    text       = models.TextField()
    is_read    = models.BooleanField(default=False)
    data       = models.JSONField(default=dict, blank=True)  # qo'shimcha ma'lumot
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering            = ['-created_at']
        verbose_name        = 'Bildirishnoma'
        verbose_name_plural = 'Bildirishnomalar'

    def __str__(self):
        return f"{self.user.phone} — {self.title}"