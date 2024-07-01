from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django_countries.fields import CountryField 
# Create your models here.

class UserP(models.Model):
    """ User profile model, containing 
    order history and delivery information """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    default_phone = models.CharField(max_length=20, blank=True, null=False)
    default_email = models.EmailField(max_length=250, blank=True, null=True)
    default_country = CountryField(blank_label='Country *', null=False, blank=True)
    default_city = models.CharField(max_length=50, blank=True, null=False)
    default_address_1 = models.CharField(max_length=75, blank=True, null=False)
    default_address_2 = models.CharField(max_length=75, blank=True, null=True)
    default_postcode = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_update_profile(sender, instance, created, **kwargs):
    """ Creates or updates a profile """

    if created:
        UserP.objects.create(user=instance)
    instance.userp.save()