from django.db import models
from django.utils import timezone
from apps.users.models import User, Address
from apps.products.models import Product, ProductVariant


class Cart(models.Model):
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def item_count(self):
        return self.items.count()


class CartItem(models.Model):
    cart     = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product  = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant  = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'product', 'variant')

    @property
    def subtotal(self):
        price = self.variant.price if self.variant and self.variant.price else self.product.price
        return price * self.quantity


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING   = 'pending',   'Tasdiqlanmoqda'
        CONFIRMED = 'confirmed', 'Tasdiqlandi'
        WAREHOUSE = 'warehouse', 'Omborga keldi'
        SHIPPED   = 'shipped',   'Yo\'lda'
        DELIVERED = 'delivered', 'Yetkazildi'
        COMPLETED = 'completed', 'Yakunlandi'
        CANCELLED = 'cancelled', 'Bekor qilindi'
        RETURNED  = 'returned',  'Qaytarildi'

    user             = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='orders')
    order_number     = models.CharField(max_length=20, unique=True, blank=True)
    status           = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    total_amount     = models.DecimalField(max_digits=14, decimal_places=2)
    delivery_cost    = models.DecimalField(max_digits=10, decimal_places=2, default=15000)
    discount_amount  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_address = models.JSONField()
    promo_code       = models.ForeignKey('payments.PromoCode', on_delete=models.SET_NULL, null=True, blank=True)
    note             = models.TextField(blank=True, verbose_name='Izoh')
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)
    completed_at     = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name        = 'Buyurtma'
        verbose_name_plural = 'Buyurtmalar'
        ordering            = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            last = Order.objects.order_by('-id').first()
            num  = (last.id + 1) if last else 1
            self.order_number = f"ORD-{timezone.now().year}-{num:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_number

    @property
    def grand_total(self):
        return self.total_amount + self.delivery_cost - self.discount_amount


class OrderItem(models.Model):
    order      = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product    = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    seller     = models.ForeignKey('users.SellerProfile', on_delete=models.SET_NULL, blank=True, null=True)
    variant    = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    name       = models.CharField(max_length=300)   # snapshot
    price      = models.DecimalField(max_digits=12, decimal_places=2)  # snapshot
    quantity   = models.PositiveIntegerField()
    is_reviewed = models.BooleanField(default=False)

    @property
    def subtotal(self):
        return self.price * self.quantity


class OrderStatusLog(models.Model):
    """Buyurtma holati o'zgarish tarixi"""
    order      = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='logs')
    status     = models.CharField(max_length=12)
    note       = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Return(models.Model):
    class Status(models.TextChoices):
        PENDING  = 'pending',  'Ko\'rib chiqilmoqda'
        APPROVED = 'approved', 'Tasdiqlandi'
        REJECTED = 'rejected', 'Rad etildi'
        RETURNED = 'returned', 'Qaytarildi'

    class Reason(models.TextChoices):
        WRONG_PHOTO = 'wrong_photo', 'Rasm bilan mos emas'
        DEFECTIVE   = 'defective',   'Nuqsonli mahsulot'
        WRONG_SIZE  = 'wrong_size',  'Noto\'g\'ri o\'lcham'
        OTHER       = 'other',       'Boshqa'

    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='returns')
    reason     = models.CharField(max_length=15, choices=Reason.choices)
    description = models.TextField(blank=True)
    status     = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Qaytarish: {self.order_item.order.order_number}"


class Review(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    product    = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    order_item = models.OneToOneField(OrderItem, on_delete=models.CASCADE)
    rating     = models.PositiveSmallIntegerField()
    text       = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Mahsulot reytingini yangilash
        from django.db.models import Avg
        product = self.product
        agg     = Review.objects.filter(product=product).aggregate(avg=Avg('rating'))
        product.rating       = agg['avg'] or 0
        product.review_count = Review.objects.filter(product=product).count()
        product.save(update_fields=['rating', 'review_count'])