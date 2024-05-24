from django.shortcuts import render
from .models import Product

# Create your views here.

def every_product(request):
    """ A view to show all the products """

    products = Product.objects.all()
    context = {
        'products': products,
    }
    return render(request, 'products/products.html', context)