from celery import shared_task
from django.conf import settings
from decimal import Decimal


@shared_task
def process_seller_payment(order_id):
    """Buyurtma completed bo'lganda sotuvchi balansini to'ldirish"""
    from orders.models import Order
    from .models import SellerBalance

    try:
        order       = Order.objects.get(pk=order_id)
        fee_percent = Decimal(settings.PLATFORM_FEE_PERCENT) / 100

        sellers = {}
        for item in order.items.all():
            if not item.seller:
                continue
            if item.seller.id not in sellers:
                sellers[item.seller.id] = {'seller': item.seller, 'amount': Decimal(0)}
            sellers[item.seller.id]['amount'] += item.subtotal

        for data in sellers.values():
            seller    = data['seller']
            gross     = data['amount']
            fee       = gross * fee_percent
            net       = gross - fee

            SellerBalance.objects.create(
                seller=seller, order=order,
                amount=net, type='credit',
                note=f"Buyurtma #{order.order_number}, fee: {fee}"
            )
            seller.balance += net
            seller.total_sales += 1
            seller.save(update_fields=['balance', 'total_sales'])

    except Order.DoesNotExist:
        pass