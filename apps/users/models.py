from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra):
        if not phone:
            raise ValueError('Telefon raqam kiritilishi shart')

        phone = ''.join(filter(str.isdigit, phone))

        if len(phone) == 9:
            phone = '998' + phone

        phone = '+' + phone

        user = self.model(phone=phone, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        extra.setdefault('role', 'admin')
        return self.create_user(phone, password, **extra)

class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        BUYER  = 'buyer',  'Xaridor'
        SELLER = 'seller', 'Sotuvchi'
        ADMIN  = 'admin',  'Admin'

    phone      = models.CharField(max_length=15, unique=True, verbose_name='Telefon')
    email      = models.EmailField(blank=True, null=True, verbose_name='Email')
    first_name = models.CharField(max_length=100, blank=True, verbose_name='Ism')
    last_name  = models.CharField(max_length=100, blank=True, verbose_name='Familiya')
    role       = models.CharField(max_length=10, choices=Role.choices, default=Role.BUYER)
    avatar     = models.ImageField(upload_to='avatars/', blank=True, null=True)

    is_active    = models.BooleanField(default=True)
    is_staff     = models.BooleanField(default=False)
    date_joined  = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD  = 'phone'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name        = 'Foydalanuvchi'
        verbose_name_plural = 'Foydalanuvchilar'



    def __str__(self):
        return f"{self.phone} ({self.get_role_display()})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.phone


class SellerProfile(models.Model):
    user        = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seller_profile')
    shop_name   = models.CharField(max_length=200, verbose_name='Do\'kon nomi')
    description = models.TextField(blank=True, verbose_name='Tavsif')
    logo        = models.ImageField(upload_to='shops/logos/', blank=True, null=True)
    balance     = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='Balans')
    is_approved = models.BooleanField(default=False, verbose_name='Tasdiqlangan')
    rating      = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_sales = models.PositiveIntegerField(default=0, verbose_name='Jami sotuvlar')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Sotuvchi profili'
        verbose_name_plural = 'Sotuvchi profillari'

    def __str__(self):
        return self.shop_name


class Address(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    title      = models.CharField(max_length=100, verbose_name='Nom (Uy, Ish...)')
    city       = models.CharField(max_length=100, verbose_name='Shahar')
    district   = models.CharField(max_length=100, verbose_name='Tuman')
    street     = models.CharField(max_length=255, verbose_name='Ko\'cha va uy')
    latitude   = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude  = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    is_default = models.BooleanField(default=False, verbose_name='Asosiy manzil')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Manzil'
        verbose_name_plural = 'Manzillar'

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.phone} — {self.title}"
