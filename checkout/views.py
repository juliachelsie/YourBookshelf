from django.shortcuts import render, reverse, redirect
from django.contrib import messages
from .forms import orderForm


def checkout(request):
    shoppingbag = request.session.get('shoppingbag', {})
    if not shoppingbag:
        messages.error(request, "Your shopping bag is empty at the moment")
        return redirect(reverse('products'))

    order_form = orderForm()
    template = 'checkout/checkout.html'
    context = {
        'order_form' : order_form,
    }

    return render(request, template, context)