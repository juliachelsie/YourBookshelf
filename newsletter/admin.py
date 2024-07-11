from django.contrib import admin
from .models import Contact


class OrderItemAdmin(admin.TabularInline):
    model = Contact

    admin.site.register(Contact)
