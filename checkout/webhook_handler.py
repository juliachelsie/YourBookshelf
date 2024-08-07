from django.http import HttpResponse
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from .models import Order, orderItem
from products.models import Product
from profiles.models import UserP

import json
import time
import stripe


class WH_Handler:
    """ Handles Stripe Webhooks """
    def __init__(self, request):
        self.request = request

    def _confirmation_email(self, order):
        """ Sends the user a confirmation email after buy """
        shopper_email = order.email
        subject = render_to_string(
            'checkout/confirmation_email/email_subject.txt',
            {'order': order})

        body = render_to_string(
            'checkout/confirmation_email/email_body.txt',
            {'order': order, 'company_email': settings.DEFAULT_FROM_EMAIL})

        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [shopper_email]
        )

    def handle_events(self, event):
        """ Handles generic/unexpected/unknown webhook event """

        return HttpResponse(
            content=f'Unhandled Webhook received: {event["type"]}',
            status=200
        )

    def handle_payment_succeeded(self, event):
        """ Handles payment_intent.succeeded webhooks from Stripe """
        intent = event.data.object
        pid = intent.id
        shoppingbag = intent.metadata.shoppingbag
        save_info = intent.metadata.save_info

        # Get the Charge object
        stripe_charge = stripe.Charge.retrieve(
         intent.latest_charge
        )

        billing_details = stripe_charge.billing_details
        shipping_details = intent.shipping
        grand_total = round(stripe_charge.amount / 100, 2)

        for field, value in shipping_details.address.items():
            if value == "":
                shipping_details.address[field] = None

        user_profile = None
        username = intent.metadata.username
        if username != 'AnonymousUser':
            user_profile = UserP.objects.get(user__username=username)
            if save_info:
                user_profile.default_phone = shipping_details.phone
                user_profile.default_country = shipping_details.address.country
                user_profile.default_postcode = shipping_details.address.postal_code
                user_profile.default_city = shipping_details.address.city
                user_profile.default_address_1 = shipping_details.address.line1
                user_profile.default_address_2 = shipping_details.address.line2
                user_profile.default_county = shipping_details.address.state
                user_profile.save()

        order_exists = False
        attempt = 1
        while attempt <= 5:
            try:
                order = Order.objects.get(
                    first_name__iexact=shipping_details.name,
                    last_name__iexact=shipping_details.name,
                    email__iexact=billing_details.email,
                    phone__iexact=shipping_details.phone,
                    country__iexact=shipping_details.address.country,
                    postcode__iexact=shipping_details.address.postal_code,
                    city__iexact=shipping_details.address.city,
                    address_1__iexact=shipping_details.address.line1,
                    address_2__iexact=shipping_details.address.line2,
                    county__iexact=shipping_details.address.state,
                    grand_total__iexact=grand_total,
                    OG_shoppingbag=shoppingbag,
                    stripe_pid=pid,
                )
                order_exists = True
                break
            except Order.DoesNotExist:
                attempt += 1
                time.sleep(1)
        if order_exists:
            self._confirmation_email(order)
            return HttpResponse(
                    content=f'Webhook received: {event["type"]} | Success: Verified order already in database',
                    status=200)
        else:
            order = None
            try:
                order = Order.objects.create(
                        first_name=shipping_details.name,
                        last_name=shipping_details.name,
                        profile=user_profile,
                        email=billing_details.email,
                        phone=shipping_details.phone,
                        country=shipping_details.address.country,
                        postcode=shipping_details.address.postal_code,
                        city=shipping_details.address.city,
                        address_1=shipping_details.address.line1,
                        address_2=shipping_details.address.line2,
                        county=shipping_details.address.state,
                        OG_shoppingbag=shoppingbag,
                        stripe_pid=pid,
                )
                for item_id, item_data in json.loads(shoppingbag).items():
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
            except Exception as e:
                if order:
                    order.delete()
                return HttpResponse(content=f'Webhook received: {event["type"]} | ERROR: {e}',
                                    status=500)
        self._confirmation_email(order)
        return HttpResponse(
            content=f'Webhook received: {event["type"]} | Success: Created order in webhook',
            status=200)

    def handle_payment_failed(self, event):
        """ Handles payment_intent.failed webhooks from Stripe """

        return HttpResponse(
            content=f'Payment Failed Webhook received: {event["type"]}',
            status=200
        )
