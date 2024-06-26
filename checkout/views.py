from django.shortcuts import render, reverse, redirect
from django.contrib import messages
from django.conf import settings
from .forms import orderForm
from shoppingbag.contexts import shoppingbag_contents
import stripe

def checkout(request):
    shoppingbag = request.session.get('shoppingbag', {})
    if not shoppingbag:
        messages.error(request, "Your shopping bag is empty at the moment")
        return redirect(reverse('products'))


    shoppingbag_now = shoppingbag_contents(request)
    total = shoppingbag_now['grand_total']
    stripe_total = round(total * 100)
    order_form = orderForm()
    template = 'checkout/checkout.html'
    context = {
        'order_form' : order_form,
        'stripe_public_key' : 'pk_test_51OKevjGkJ5U3ree3hDekfwjx55kbeLxkqd4ZFixTfFSX85MVHCPBSMaJxvG26rq1QUzHyGTD4Pw4A12o5O2hciZm00abo7KSoY',
        'client_secret': 'test client secret',
    }

    return render(request, template, context)