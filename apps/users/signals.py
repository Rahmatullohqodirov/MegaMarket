from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, SellerProfile


@receiver(post_save, sender=User)
def create_seller_profile(sender, instance, created, **kwargs):
    if created and instance.role == 'seller':
        SellerProfile.objects.get_or_create(
            user=instance,
            defaults={'shop_name': f"{instance.full_name} Shop"}
        )