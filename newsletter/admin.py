from django.contrib import admin
from .models import Contact

# Register your models here.
class OrderItemAdmin(admin.TabularInline):
    model = Contact

    admin.site.register(Contact)