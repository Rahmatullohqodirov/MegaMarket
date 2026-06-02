from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order


@receiver(post_save, sender=Order)
def notify_on_status_change(sender, instance, created, **kwargs):
    """Holat o'zgarganda Celery task ishga tushadi"""
    if not created:
        from notifications.tasks import send_order_status_notification
        send_order_status_notification.delay(instance.id, instance.status)