from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import orderItem

@receiver(post_save, sender=orderItem)
def update_on_save(sender, instance, created, **kwargs):
    """ Updates order total on lineitem update/create """
    instance.order.update_total()

@receiver(post_delete, sender=orderItem)
def update_on_save(sender, instance, **kwargs):
    """ Updates order total on lineitem delete """
    instance.order.update_total()