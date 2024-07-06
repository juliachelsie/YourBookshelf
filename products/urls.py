from django.urls import path
from . import views

urlpatterns = [
    path('', views.every_product, name='products'),
    path('<int:product_id>', views.product_info, name='product_info'),
    path('add/', views.admin_add_product, name='admin_add_product'),
    path('modify/<int:product_id>', views.modify_product, name='modify_product'),

]