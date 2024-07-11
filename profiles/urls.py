from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_profile, name='user_profile'),
    path('o_history/<order_number>', views.o_history, name='o_history'),
]
