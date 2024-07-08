from django.shortcuts import render, reverse, redirect, get_object_or_404, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from .forms import orderForm
from profiles.forms import ProfileForm
from profiles.forms import UserP
from products.models import Product
from .models import orderItem, Order
from shoppingbag.contexts import shoppingbag_contents
import stripe
import json


@require_POST
def cache_checkout_data(request):
    try:
        pid = request.POST.get('client_secret').split('_secret')[0]
        stripe.api_key = settings.STRIPE_SECRET_KEY
        stripe.PaymentIntent.modify(pid, metadata={
            'shoppingbag': json.dumps(request.session.get('shoppingbag', {})),
            'save_info': request.POST.get('save_info'),
            'username': request.user,
        })
        return HttpResponse(status=200)
    except Exception as e:
        messages.error(request, 'Your payment cannot be processed \
        right now, Please try again later.')
        return HttpResponse(content=e, status=400)


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
            order = order_form.save(commit=False)
            pid = request.POST.get('client_secret').split('_secret')[0]
            order.stripe_pid = pid
            order.OG_shoppingbag = json.dumps(shoppingbag)
            order.save()
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
            return redirect(reverse('checkout_win', args=[order.order_number]))
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

        if request.user.is_authenticated:
            try:
                profile=UserP.objects.get(user=request.user)
                order_form=orderForm(initial={
                    'first_name': profile.default_first_name,
                    'last_name': profile.default_last_name,
                    'email': profile.default_email,
                    'phone': profile.default_phone,
                    'address_1': profile.default_address_1,
                    'address_2': profile.default_address_2,
                    'postcode': profile.default_postcode,
                    'city': profile.default_city,
                    'country': profile.default_country,
                    'city': profile.default_city,
                })
            except UserP.DoesNotExist:
                order_form = orderForm()
        else:
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
    """ Handles successful checkouts """

    save_info = request.session.get('save_info')
    order = get_object_or_404(Order, order_number=order_number)
    user_profile= None

    if request.user.is_authenticated:
        user_profile = UserP.objects.get(user=request.user)
        order.profile = user_profile
        order.save()

    if save_info and user_profile:
        user_data = {
            'default_first_name': order.first_name,
            'default_last_name': order.last_name,
            'default_phone': order.phone,
            'default_email': order.email,
            'default_address_1': order.address_1,
            'default_address_2': order.address_2,
            'default_postcode': order.postcode,
            'default_city': order.city,
            'default_county': order.county,
            'default_country': order.country,
        }

        profile_form = ProfileForm(user_data, instance=user_profile)
        if profile_form.is_valid():
            profile_form.save()

    messages.success(request, f'Order successful! \
    Your order number is {order_number}. You will revieve a confirmation\
    email to {order.email}.')

    if 'shoppingbag' in request.session:
        del request.session['shoppingbag']

    template ='checkout/checkout_win.html'
    context = {
        'order': order,
    }

    return render(request, template, context)


