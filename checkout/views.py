from django.shortcuts import render, reverse, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from .forms import orderForm
from products.models import Product
from .models import orderItem
from shoppingbag.contexts import shoppingbag_contents
import stripe

def checkout(request):
    stripe_public_key = settings.STRIPE_PUBLIC_KEY
    stripe_secret_key = settings.STRIPE_SECRET_KEY

    if request.method == 'POST':
        shoppingbag = request.session.get('shoppingbag', {})
        formData = {
            'first_name': request.POST['first_name'],
            'last_name': request.POST['last_name'],
            'email': request.POST['email'],
            'phone': request.POST['phone'],
            'country': request.POST['country'],
            'postcode': request.POST['postcode'],
            'city': request.POST['city'],
            'address_1': request.POST['address_1'],
            'address_2': request.POST['address_2'],
            'county': request.POST['county'],
        }
        order_form=orderForm(formData)
        if order_form.is_valid():
            order_form.save()
            for item_id, item_data in shoppingbag.items():
                try:
                    product = Product.objects.get(id=item_id)
                    if isinstance(item_data, int):
                        order_item = orderItem(
                            order=order,
                            product=product,
                            quantity=item_data,
                        )
                        order_item.save()
                    else:
                        for size, quantity in item_data['items_by_size'].items():
                            order_item = orderItem(
                                order=order,
                                product=product,
                                quantity=quantity,
                                product_size=size,
                            )
                            order_item.save()
                except Product.DoesNotExist:
                    messages.error(request, (
                        "One of Your selected products were not found in our database." 
                        "Please give us a call and we will help You!")
                    )
                    order.delete()
                    return redirect(reverse('view_shoppingbag'))

            request.session['save_info'] = 'save-info' in request.POST
            return resirect(reverse('checkout_win', args=[order.order_]))
        else:
            messages.error(request, 'An error occured with Your form, please double check Your information.')
    else:
        shoppingbag = request.session.get('shoppingbag', {})
        if not shoppingbag:
            messages.error(request, "Your shopping bag is empty at the moment")
            return redirect(reverse('products'))

        shoppingbag_now = shoppingbag_contents(request)
        total = shoppingbag_now['grand_total']
        stripe_total = round(total * 100)
        stripe.api_key = stripe_secret_key
        intent = stripe.PaymentIntent.create(
            amount=stripe_total,
            currency=settings.STRIPE_CURRENCY,
        )

        order_form = orderForm()

    if not stripe_public_key:
        messages.warning(request, 'Stripe public key is missing, did you set it in your environment?')
    
    template = 'checkout/checkout.html'
    context = {
        'order_form' : order_form,
        'stripe_public_key' : stripe_public_key,
        'client_secret': intent.client_secret,
    }

    return render(request, template, context)

def checkout_win(request, order_number):
    """ Handlesuccessful checkouts """

    save_info = request.session.get('save_info')
    order = get_object_or_404(Order, order_number=order_number)
    messages.success(request, f'Order successful! \
    Your order number is {order_number}. You will revieve a confirmation\
    email to {order.email}')

    if 'shoppingbag' in request.session:
        del request.session['shoppingbag']

    template ='checkout/checkout_win.html'
    context = {
        'order': order,
    }

    return render(request, template, context)


