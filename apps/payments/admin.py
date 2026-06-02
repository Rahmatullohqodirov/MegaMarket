from django.contrib import admin
from .models import Payment, SellerBalance, PromoCode, WithdrawalRequest


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display   = ('order', 'provider', 'status', 'amount', 'transaction_id', 'paid_at', 'created_at')
    list_filter    = ('provider', 'status')
    search_fields  = ('order__order_number', 'transaction_id')
    readonly_fields = ('order', 'provider', 'amount', 'transaction_id', 'provider_data', 'paid_at', 'created_at')


@admin.register(SellerBalance)
class SellerBalanceAdmin(admin.ModelAdmin):
    list_display  = ('seller', 'type', 'amount', 'order', 'created_at')
    list_filter   = ('type',)
    search_fields = ('seller__shop_name', 'order__order_number')
    readonly_fields = ('seller', 'order', 'amount', 'type', 'created_at')


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display  = ('code', 'discount_percent', 'max_uses', 'min_amount','used_count', 'is_active', 'expires_at')
    list_filter   = ('is_active',)
    search_fields = ('code',)


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display  = ('seller', 'amount', 'card_number', 'status', 'created_at')
    list_filter   = ('status',)
    search_fields = ('seller__shop_name',)
    actions       = ['approve_withdrawals', 'reject_withdrawals']

    @admin.action(description='Tasdiqlash')
    def approve_withdrawals(self, request, queryset):
        for wr in queryset.filter(status='pending'):
            wr.status = 'approved'
            wr.save()
            seller = wr.seller
            seller.balance -= wr.amount
            seller.save(update_fields=['balance'])
        self.message_user(request, "To'lovlar tasdiqlandi.")

    @admin.action(description='Rad etish')
    def reject_withdrawals(self, request, queryset):
        queryset.filter(status='pending').update(status='rejected')
        self.message_user(request, "To'lovlar rad etildi.")