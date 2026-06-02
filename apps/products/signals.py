from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import ProductVariant, Product


@receiver(post_save, sender=ProductVariant)
def update_product_stock(sender, instance, **kwargs):
    """Variant stoki o'zgarganda mahsulot stockini yangilash"""
    product       = instance.product
    product.stock = sum(v.stock for v in product.variants.all())
    product.save(update_fields=['stock'])


@receiver(post_delete, sender=ProductVariant)
def update_stock_on_delete(sender, instance, **kwargs):
    """Variant o'chirilganda stockni yangilash"""
    try:
        product       = instance.product
        product.stock = sum(v.stock for v in product.variants.all())
        product.save(update_fields=['stock'])
    except Exception:
        pass