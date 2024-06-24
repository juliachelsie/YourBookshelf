from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.view_shoppingbag, name='view_shoppingbag'),
    path('add/<item_id>/', views.add_to_shoppingbag, name='add_to_shoppingbag'),
    path('modify/<item_id>/', views.modify_shoppingbag, name='modify_shoppingbag'),
    path('remove/<item_id>/', views.remove_from_shoppingbag, name='remove_from_shoppingbag'),
]