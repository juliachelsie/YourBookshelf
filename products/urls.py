from django.urls import path
from . import views

urlpatterns = [
    path('', views.every_product, name='products'),
]