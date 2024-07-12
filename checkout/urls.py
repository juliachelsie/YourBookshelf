from django.contrib import admin
from django.urls import path
from . import views
from .webhooks import webhook

urlpatterns = [
    path('/', views.checkout, name='checkout'),
    path('checkout_win/<order_number>/', views.checkout_win,
         name='checkout_win'),
    path('cache_checkout_data/', views.cache_checkout_data,
         name='cache_checkout_data'),
    path('wh/', webhook, name='webhook'),
]
