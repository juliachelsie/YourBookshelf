from django.contrib import admin
from .models import Order, orderItem


class OrderItemAdmin(admin.TabularInline):
    model = orderItem
    readonly_fields = ('order_item_total',)


class OrderAdmin(admin.ModelAdmin):
    inlines = (OrderItemAdmin,)
    readonly_fields = ('order_number', 'date',
                       'delivery', 'order_total',
                       'grand_total', 'OG_shoppingbag',
                       'stripe_pid')

    fields = ('profile', 'order_number', 'date', 'first_name', 'last_name',
              'email', 'phone', 'country', 'postcode', 'city',
              'address_1', 'address_2', 'county', 'delivery',
              'order_total', 'grand_total', 'OG_shoppingbag',
              'stripe_pid')

    list_display = ('order_number', 'date', 'first_name', 'last_name',
                    'order_total', 'delivery', 'grand_total',)
    ordering = ('-date',)


admin.site.register(Order, OrderAdmin)
