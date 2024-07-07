from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.contact_view, name='newsletter'),
    path('contact/', views.contact_view, name='contact_view'),
]