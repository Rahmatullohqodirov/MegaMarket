from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, SellerProfile, Address


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display   = ('phone', 'full_name', 'role', 'is_active', 'date_joined')
    list_filter    = ('role', 'is_active', 'is_staff')
    search_fields  = ('phone', 'first_name', 'last_name', 'email')
    ordering       = ('-date_joined',)
    fieldsets      = (
        (None,           {'fields': ('phone', 'password')}),
        ('Shaxsiy',      {'fields': ('first_name', 'last_name', 'email', 'avatar')}),
        ('Rol va Huquq', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Sana',         {'fields': ('date_joined', 'last_login')}),
    )
    add_fieldsets  = (
        (None, {
            'classes': ('wide',),
            'fields':  ('phone', 'password1', 'password2', 'role'),
        }),
    )
    readonly_fields = ('date_joined', 'last_login')


@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display   = ('shop_name', 'user', 'balance', 'is_approved', 'rating', 'total_sales', 'created_at')
    list_filter    = ('is_approved',)
    search_fields  = ('shop_name', 'user__phone')
    readonly_fields = ('balance', 'rating', 'total_sales', 'created_at')
    actions        = ['approve_sellers']

    @admin.action(description='Tanlangan sotuvchilarni tasdiqlash')
    def approve_sellers(self, request, queryset):
        count = queryset.update(is_approved=True)
        self.message_user(request, f"{count} ta sotuvchi tasdiqlandi.")


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display  = ('user', 'title', 'city', 'district', 'is_default')
    list_filter   = ('city', 'is_default')
    search_fields = ('user__phone', 'city', 'district', 'street')