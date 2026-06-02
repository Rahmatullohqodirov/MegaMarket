from django.db import models
from django.utils.text import slugify
from apps.users.models import User, SellerProfile


class Category(models.Model):
    name      = models.CharField(max_length=200, verbose_name='Nom')
    slug      = models.SlugField(unique=True, blank=True)
    parent    = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    image     = models.ImageField(upload_to='categories/', blank=True, null=True)
    order     = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name        = 'Kategoriya'
        verbose_name_plural = 'Kategoriyalar'
        ordering            = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    seller       = models.ForeignKey('users.SellerProfile', on_delete=models.CASCADE, related_name='products')
    category     = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    name         = models.CharField(max_length=300, verbose_name='Nom')
    slug         = models.SlugField(unique=True, blank=True, max_length=350)
    description  = models.TextField(verbose_name='Tavsif')
    price        = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Narx')
    old_price    = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name='Eski narx')
    stock        = models.PositiveIntegerField(default=0, verbose_name='Ombordagi miqdor')
    is_active    = models.BooleanField(default=True, verbose_name='Faol')
    is_approved  = models.BooleanField(default=False, verbose_name='Tasdiqlangan')
    rating       = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    review_count = models.PositiveIntegerField(default=0)
    sold_count   = models.PositiveIntegerField(default=0, verbose_name='Sotilganlar soni')
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Mahsulot'
        verbose_name_plural = 'Mahsulotlar'
        ordering            = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug      = base_slug
            counter   = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def discount_percent(self):
        if self.old_price and self.old_price > self.price:
            return int((1 - self.price / self.old_price) * 100)
        return 0

    @property
    def in_stock(self):
        return self.stock > 0


class ProductImage(models.Model):
    product  = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image    = models.ImageField(upload_to='products/')
    is_main  = models.BooleanField(default=False, verbose_name='Asosiy rasm')
    order    = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def save(self, *args, **kwargs):
        # Faqat bitta asosiy rasm bo'lishi mumkin
        if self.is_main:
            ProductImage.objects.filter(product=self.product, is_main=True).update(is_main=False)
        super().save(*args, **kwargs)


class ProductVariant(models.Model):
    product  = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    color    = models.CharField(max_length=50, blank=True, verbose_name='Rang')
    size     = models.CharField(max_length=20, blank=True, verbose_name='O\'lcham')
    stock    = models.PositiveIntegerField(default=0)
    price    = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    class Meta:
        verbose_name        = 'Variant'
        verbose_name_plural = 'Variantlar'

    def __str__(self):
        return f"{self.product.name} — {self.color} {self.size}"


class Wishlist(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    product    = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        verbose_name    = 'Saqlangan'

    def __str__(self):
        return f"{self.user.phone} → {self.product.name}"


class Banner(models.Model):
    class Position(models.TextChoices):
        MAIN   = 'main',   'Bosh sahifa'
        PROMO  = 'promo',  'Aksiya'
        BOTTOM = 'bottom', 'Pastki'

    title     = models.CharField(max_length=200)
    image     = models.ImageField(upload_to='banners/')
    link      = models.URLField(blank=True)
    position  = models.CharField(max_length=10, choices=Position.choices, default=Position.MAIN)
    order     = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(blank=True, null=True)
    ends_at   = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title