from celery import shared_task
import requests
from django.conf import settings


def _create_notification(user_id, type_, title, text, data=None):
    """Ichki yordamchi funksiya"""
    from .models import Notification
    from users.models import User
    try:
        user = User.objects.get(pk=user_id)
        Notification.objects.create(user=user, type=type_, title=title, text=text, data=data or {})
    except User.DoesNotExist:
        pass


def _send_sms(phone: str, message: str):
    """Eskiz SMS API"""
    try:
        # Token olish
        token_resp = requests.post('https://notify.eskiz.uz/api/auth/login', data={
            'email':    settings.ESKIZ_EMAIL,
            'password': settings.ESKIZ_PASSWORD,
        }, timeout=10)
        token = token_resp.json().get('data', {}).get('token')
        if not token:
            return

        # SMS yuborish
        requests.post('https://notify.eskiz.uz/api/message/sms/send', headers={
            'Authorization': f'Bearer {token}'
        }, data={
            'mobile_phone': phone,
            'message':      message,
            'from':         '4546',
        }, timeout=10)
    except Exception:
        pass


# ─── Buyurtma ─────────────────────────────────────────────────────────────────

@shared_task
def send_order_status_notification(order_id, event='new_order'):
    from orders.models import Order

    STATUS_MESSAGES = {
        'new_order': ('📦 Yangi buyurtma',      'Buyurtmangiz qabul qilindi!'),
        'confirmed': ('✅ Tasdiqlandi',           'Buyurtmangiz tasdiqlandi!'),
        'warehouse': ('📦 Omborga keldi',         'Mahsulot omborga yetib keldi.'),
        'shipped':   ('🚚 Yo\'lda',              'Buyurtmangiz yo\'lga chiqdi!'),
        'delivered': ('🎉 Yetkazildi',            'Buyurtmangiz yetkazildi. Rahmat!'),
        'completed': ('✅ Yakunlandi',            'Buyurtma yakunlandi. Izoh qoldiring!'),
        'cancelled': ('❌ Bekor qilindi',         'Buyurtmangiz bekor qilindi.'),
    }

    try:
        order   = Order.objects.select_related('user').get(pk=order_id)
        title, text = STATUS_MESSAGES.get(event, ('📌 Yangilik', 'Buyurtma yangilandi'))
        _create_notification(order.user.id, 'order', title, f"{text} ({order.order_number})", {'order_id': order_id})
        _send_sms(order.user.phone, f"Bozor.uz: {text} #{order.order_number}")
    except Exception:
        pass


@shared_task
def send_seller_approved_notification(user_id):
    _create_notification(user_id, 'seller', '✅ Hisob tasdiqlandi', 'Sotuvchi hisobingiz tasdiqlandi! Mahsulot qo\'sha boshlang.')
    from users.models import User
    try:
        user = User.objects.get(pk=user_id)
        _send_sms(user.phone, 'Bozor.uz: Sotuvchi hisobingiz tasdiqlandi!')
    except User.DoesNotExist:
        pass


@shared_task
def send_product_approved_notification(product_id):
    from products.models import Product
    try:
        product = Product.objects.select_related('seller__user').get(pk=product_id)
        user_id = product.seller.user.id
        _create_notification(user_id, 'product', '✅ Mahsulot tasdiqlandi', f"'{product.name}' mahsulotingiz tasdiqlandi va saytda ko'rinmoqda.", {'product_id': product_id})
    except Product.DoesNotExist:
        pass


@shared_task
def send_promo_notification(user_ids: list, promo_code: str, discount: int):
    """Barcha foydalanuvchilarga promo xabar"""
    for uid in user_ids:
        _create_notification(uid, 'promo', '🎉 Maxsus taklif!', f"{promo_code} kodi bilan {discount}% chegirma!")


@shared_task
def auto_complete_orders():
    """Har kecha: 7 kun o'tgan delivered buyurtmalarni completed qilish"""
    from orders.models import Order
    from django.utils import timezone
    from datetime import timedelta

    cutoff  = timezone.now() - timedelta(days=7)
    orders  = Order.objects.filter(status='delivered', updated_at__lte=cutoff)
    count   = 0
    for order in orders:
        order.status       = 'completed'
        order.completed_at = timezone.now()
        order.save(update_fields=['status', 'completed_at'])
        from payments.tasks import process_seller_payment
        process_seller_payment.delay(order.id)
        send_order_status_notification.delay(order.id, 'completed')
        count += 1
    return f"{count} ta buyurtma yakunlandi"


@shared_task
def send_daily_report_to_admin():
    """Har kecha 22:00 da admin uchun kunlik hisobot"""
    from orders.models import Order
    from users.models import User
    from django.utils import timezone
    from django.db.models import Sum, Count

    today  = timezone.now().date()
    orders = Order.objects.filter(created_at__date=today)
    total  = orders.aggregate(s=Sum('total_amount'))['s'] or 0
    count  = orders.count()

    admins = User.objects.filter(role='admin')
    for admin in admins:
        _create_notification(
            admin.id, 'system',
            f'📊 Kunlik hisobot — {today}',
            f"Bugun: {count} ta buyurtma, {total:,.0f} so'm daromad."
        )