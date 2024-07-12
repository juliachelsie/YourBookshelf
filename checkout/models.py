import uuid
from django.db import models
from django.db.models import Sum
from django.conf import settings
from products.models import Product
from django_countries.fields import CountryField
from profiles.models import UserP

# Create your models here.


class Order(models.Model):
    order_number = models.CharField(max_length=200, null=False, editable=False)
    profile = models.ForeignKey(UserP, on_delete=models.SET_NULL,
                                related_name='orders', blank=True, null=True)
    first_name = models.CharField(max_length=50, null=False, blank=False)
    last_name = models.CharField(max_length=50, blank=False, null=False)
    phone = models.CharField(max_length=20, blank=False, null=False)
    email = models.EmailField(max_length=250, blank=False, null=True)
    country = CountryField(blank_label='Country *', null=False, blank=False)
    city = models.CharField(max_length=50, blank=False, null=False)
    address_1 = models.CharField(max_length=75, blank=False, null=False)
    address_2 = models.CharField(max_length=75, blank=True, null=True)
    postcode = models.CharField(max_length=20, null=True, blank=True)
    county = models.CharField(max_length=75, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    delivery = models.DecimalField(max_digits=6,
                                   decimal_places=2, null=False, default=0)
    order_total = models.DecimalField(max_digits=10, decimal_places=2,
                                      null=False, default=0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2,
                                      null=False, default=0)
    OG_shoppingbag = models.TextField(blank=False, null=False, default='')
    stripe_pid = models.CharField(blank=False, null=False, max_length=250,
                                  default='')

    def _produce_order_number(self):
        """ Produces a random unique order number using UUID """
        return uuid.uuid4().hex.upper()

    def update_total(self):
        """ Updates grand total """
        self.order_total = self.orderitems.aggregate(Sum('order_item_total'))['order_item_total__sum'] or 0
        if self.order_total < settings.FREE_DELIVERY_THRESHOLD:
            self.delivery = self.order_total * settings.STANDARD_DELIVERY_PERCENTAGE/100
        else:
            self.delivery = 0
        self.grand_total = self.order_total + self.delivery
        self.save()

    def save(self, *args, **kwargs):
        """ Overides the original save method to set the order number """
        if not self.order_number:
            self.order_number = self._produce_order_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_number


class orderItem(models.Model):
    order = models.ForeignKey(Order, blank=False, null=False,
                              related_name='orderitems',
                              on_delete=models.CASCADE)
    product = models.ForeignKey(Product, null=False, blank=False,
                                on_delete=models.CASCADE)
    product_size = models.CharField(max_length=2, null=True,
                                    blank=True)  # A4, A5
    quantity = models.IntegerField(blank=False, null=False, default=0)
    order_item_total = models.DecimalField(max_digits=6, decimal_places=2,
                                           blank=False, null=False,
                                           editable=False)

    def save(self, *args, **kwargs):
        """ Overides the original save method to set the order lineitem
            total and updates the order total """
        self.order_item_total = self.product.price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f'SKU {self.product.sku} on order {self.order.order_number}'
