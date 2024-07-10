from unittest import mock
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.utils.encoding import force_bytes
from django.contrib.admin.sites import site as admin_site
from django.utils import timezone
from django.contrib.messages import get_messages
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.mail import send_mail
from django.contrib.sessions.middleware import SessionMiddleware
from django.db.models import Sum
from django.db.models.signals import post_save, post_delete
from django.http import HttpRequest, HttpResponse, HttpResponseNotFound
from django.conf import settings
from django_countries import countries
from django_countries.fields import Country
from decimal import Decimal, ROUND_HALF_UP
from unittest.mock import patch, Mock, MagicMock
import stripe
import json
import uuid
import time
import hashlib
import hmac

from checkout import views
from .admin import OrderAdmin, OrderItemAdmin
from .models import Order, orderItem
from .forms import orderForm
from checkout.webhooks import webhook 
from profiles.models import UserP
from profiles.forms import ProfileForm
from products.models import Product
from checkout.webhook_handler import WH_Handler


# VIEWS.PY

# Testing "checkout" from views.py
class CheckoutTestCase(TestCase):

    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(username='testuser', password='12345')

        # Create a user profile
        self.user_profile = UserP.objects.create(user=self.user, default_first_name='John', default_last_name='Doe')

        # Create sample product
        self.product = Product.objects.create(
            name='Sample Product',
            price=10.0,
            description='A sample product for testing purposes.'
        )

        # Create a shopping bag session data
        self.shoppingbag = {
            str(self.product.id): {
                'quantity': 2,
            }
        }

        # Create a mock PaymentIntent response
        self.client_secret = 'pi_mock_secret_12345'

        # Mock Stripe API key
        stripe.api_key = settings.STRIPE_SECRET_KEY

    def tearDown(self):
        # Clean up after each test if necessary
        pass

# Testing "cache_checkout_data" in views.py.

class CacheCheckoutDataViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.url = reverse('cache_checkout_data')

    @patch('checkout.views.stripe.PaymentIntent.modify')
    def test_cache_checkout_data_success(self, mock_stripe_modify):
        mock_stripe_modify.return_value = Mock()
        
        session = self.client.session
        session['shoppingbag'] = {'item1': 1, 'item2': 2}
        session.save()

        response = self.client.post(self.url, {
            'client_secret': 'pi_1Fxxxx_secret_yyyy',
            'save_info': 'on'
        })

        self.assertEqual(response.status_code, 200)
        mock_stripe_modify.assert_called_once_with(
            'pi_1Fxxxx',
            metadata={
                'shoppingbag': json.dumps({'item1': 1, 'item2': 2}),
                'save_info': 'on',
                'username': 'testuser',  # No need to convert to string in test
            }
        )

    @patch('checkout.views.stripe.PaymentIntent.modify')
    def test_cache_checkout_data_exception(self, mock_stripe_modify):
        mock_stripe_modify.side_effect = Exception('Test error')

        session = self.client.session
        session['shoppingbag'] = {'item1': 1, 'item2': 2}
        session.save()

        response = self.client.post(self.url, {
            'client_secret': 'pi_1Fxxxx_secret_yyyy',
            'save_info': 'on'
        })

        messages = list(get_messages(response.wsgi_request))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(str(messages[0]).strip(), 'Your payment cannot be processed right now, Please try again later.')

# Testing "checkout_win" in views.py.

class CheckoutWinViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.profile, created = UserP.objects.get_or_create(user=self.user)
        self.order = Order.objects.create(
            order_number='12345',
            first_name='John',
            last_name='Doe',
            phone='1234567890',
            email='john.doe@example.com',
            address_1='123 Street',
            address_2='Apt 4',
            postcode='12345',
            city='City',
            county='County',
            country='Country'
        )
        self.url = reverse('checkout_win', args=['12345'])

    def test_checkout_win_authenticated_user_with_save_info(self):
        self.client.login(username='testuser', password='12345')
        session = self.client.session
        session['save_info'] = True
        session.save()

        response = self.client.get(self.url)

        self.order.refresh_from_db()
        self.assertEqual(self.order.profile, self.profile)

        profile_data = {
            'default_first_name': 'John',
            'default_last_name': 'Doe',
            'default_phone': '1234567890',
            'default_email': 'john.doe@example.com',
            'default_address_1': '123 Street',
            'default_address_2': 'Apt 4',
            'default_postcode': '12345',
            'default_city': 'City',
            'default_county': 'County',
            'default_country': 'US',
        }

        profile_form = ProfileForm(profile_data, instance=self.profile)
        if not profile_form.is_valid():
            print(profile_form.errors)
        self.assertTrue(profile_form.is_valid())
        profile_form.save()

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'Order successful! Your order number is 12345. You will receive a confirmation email to john.doe@example.com.')

        self.assertNotIn('shoppingbag', self.client.session)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'checkout/checkout_win.html')
        self.assertContains(response, 'Order successful! Your order number is 12345.')

    def test_checkout_win_authenticated_user_without_save_info(self):
        self.client.login(username='testuser', password='12345')
        session = self.client.session
        session['save_info'] = False
        session.save()

        response = self.client.get(self.url)

        self.order.refresh_from_db()
        self.assertEqual(self.order.profile, self.profile)

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'Order successful! Your order number is 12345. You will receive a confirmation email to john.doe@example.com.')

        self.assertNotIn('shoppingbag', self.client.session)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'checkout/checkout_win.html')
        self.assertContains(response, 'Order successful! Your order number is 12345.')

    def test_checkout_win_unauthenticated_user(self):
        response = self.client.get(self.url)

        self.order.refresh_from_db()
        self.assertIsNone(self.order.profile)

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'Order successful! Your order number is 12345. You will receive a confirmation email to john.doe@example.com.')

        self.assertNotIn('shoppingbag', self.client.session)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'checkout/checkout_win.html')
        self.assertContains(response, 'Order successful! Your order number is 12345.')

        # MODELS.PY

# MODELS.PY

# Testing Order from models.py.

class OrderModelTests(TestCase):

    def setUp(self):
        self.order = Order.objects.create(order_number='12345')

    def test_create_order_item(self):
        product = Product.objects.create(name='Test Product', price=10.0)  # Adjust fields as per your Product model
        order_item = orderItem.objects.create(
            order=self.order,
            product=product,
            quantity=2,
            # Add other fields as necessary
        )

        self.assertEqual(orderItem.objects.count(), 1)
        saved_order_item = orderItem.objects.first()
        self.assertEqual(saved_order_item.order, self.order)
        self.assertEqual(saved_order_item.product, product)
        self.assertEqual(saved_order_item.quantity, 2)

    def test_update_order_item(self):
        product = Product.objects.create(name='Initial Product', price=15.0)  # Adjust fields as per your Product model
        order_item = orderItem.objects.create(
            order=self.order,
            product=product,
            quantity=1,
            # Add other fields as necessary
        )

        product_updated = Product.objects.create(name='Updated Product', price=20.0)  # Adjust fields as per your Product model
        order_item.product = product_updated
        order_item.quantity = 3
        order_item.save()

        updated_order_item = orderItem.objects.get(pk=order_item.pk)

        self.assertEqual(updated_order_item.product, product_updated)
        self.assertEqual(updated_order_item.quantity, 3)

    def test_delete_order_item(self):
        product = Product.objects.create(name='Test Product', price=10.0)  # Adjust fields as per your Product model
        order_item = orderItem.objects.create(
            order=self.order,
            product=product,
            quantity=2,
            # Add other fields as necessary
        )

        order_item.delete()
        self.assertEqual(orderItem.objects.count(), 0)

# Testing "orderItem" from models.py.

class orderItemModelTests(TestCase):

    def setUp(self):
        # Create a sample Order and Product for testing
        self.order = Order.objects.create(order_number='12345')
        self.product = Product.objects.create(name='Test Product', price=10.0)

    def test_create_order_item(self):
        # Create a new orderItem instance
        order_item = orderItem.objects.create(
            order=self.order,
            product=self.product,
            product_size='A4',
            quantity=2
        )

        # Check if orderItem was created successfully
        self.assertEqual(orderItem.objects.count(), 1)
        
        # Retrieve the saved orderItem instance
        saved_order_item = orderItem.objects.first()
        
        # Check attributes of the saved orderItem
        self.assertEqual(saved_order_item.order, self.order)
        self.assertEqual(saved_order_item.product, self.product)
        self.assertEqual(saved_order_item.product_size, 'A4')
        self.assertEqual(saved_order_item.quantity, 2)
        
        # Check if order_item_total was calculated correctly
        expected_total = self.product.price * 2
        self.assertEqual(saved_order_item.order_item_total, expected_total)

    def test_update_order_item(self):
        # Create an initial orderItem instance
        order_item = orderItem.objects.create(
            order=self.order,
            product=self.product,
            product_size='A5',
            quantity=1
        )
        
        # Update the orderItem instance
        order_item.quantity = 3
        order_item.save()
        
        # Retrieve the updated orderItem instance from the database
        updated_order_item = orderItem.objects.get(pk=order_item.pk)
        
        # Check if the update was applied correctly
        self.assertEqual(updated_order_item.quantity, 3)
        
        # Check if order_item_total was recalculated correctly
        expected_total = self.product.price * 3
        self.assertEqual(updated_order_item.order_item_total, expected_total)

    def test_delete_order_item(self):
        # Create an orderItem instance
        order_item = orderItem.objects.create(
            order=self.order,
            product=self.product,
            product_size='A4',
            quantity=2
        )
        
        # Delete the orderItem instance
        order_item.delete()
        
        # Check if the o was deleted successfully
        self.assertEqual(orderItem.objects.count(), 0)

# FORMS.PY

# Testing orderForm from forms.py

class orderFormTests(TestCase):

    def setUp(self):
        self.form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone': '1234567890',
            'country': 'US',
            'address_1': '123 Main St',
            'address_2': 'Apt 1',
            'city': 'New York',
            'postcode': '10001',
            'county': 'NY',
        }

    def test_form_initialization(self):
        # Initialize the form with form data
        form = orderForm(data={})
        
        # Check if the form is initialized correctly
        self.assertTrue(form.is_bound)
        self.assertFalse(form.is_valid())  # Form should be invalid because it's not fully populated

    def test_placeholder_attributes(self):
        # Initialize an empty form
        form = orderForm()
        
        # Check placeholder attributes
        expected_placeholders = {
            'first_name': 'First Name *',
            'last_name': 'Last Name *',
            'email': 'Email Address *',
            'phone': 'Phone number *',
            'country': 'Country *',
            'address_1' : 'Address 1 *',
            'address_2' : 'Address 2',
            'city': 'City *',
            'postcode': 'Postal Code',
            'county': 'County or state',
        }
        
        for field_name, expected_placeholder in expected_placeholders.items():
            self.assertEqual(form.fields[field_name].widget.attrs['placeholder'], expected_placeholder)

    def test_widget_attributes(self):
        # Initialize an empty form
        form = orderForm()
        
        # Check widget attributes
        for field_name, field in form.fields.items():
            self.assertEqual(form.fields[field_name].widget.attrs.get('class'), 'stripe-style-input')

        # Check autofocus attribute
        self.assertTrue(form.fields['first_name'].widget.attrs.get('autofocus', False))


# SIGNALS.PY

# Testing "update_on_save" from signals.py

class OrderItemSignalTests(TestCase):

    def setUp(self):
        # Create an Order instance to use in tests
        self.order = Order.objects.create()
        # Create a Product instance to use in tests
        self.product = Product.objects.create(name='Test Product', price=10)

    @patch('checkout.models.Order.update_total')
    def test_update_on_save_signal_create(self, mock_update_total):
        # Create a new orderItem and check if update_total is called
        order_item = orderItem.objects.create(order=self.order, product=self.product, quantity=1)
        self.assertTrue(mock_update_total.called)
        self.assertEqual(mock_update_total.call_count, 1)

    @patch('checkout.models.Order.update_total')
    def test_update_on_save_signal_update(self, mock_update_total):
        # Create an orderItem instance
        order_item = orderItem.objects.create(order=self.order, product=self.product, quantity=1)
        # Reset the mock call count
        mock_update_total.reset_mock()
        # Update the orderItem and check if update_total is called
        order_item.quantity = 2
        order_item.save()
        self.assertTrue(mock_update_total.called)
        self.assertEqual(mock_update_total.call_count, 1)


# Testing "update_on_delete" from signals.py

class OrderItemSignalTests(TestCase):

    def setUp(self):
        # Create an Order instance to use in tests
        self.order = Order.objects.create()
        # Create a Product instance to use in tests
        self.product = Product.objects.create(name='Test Product', price=10)

    @patch('checkout.models.Order.update_total')
    def test_update_on_delete_signal(self, mock_update_total):
        # Create an orderItem instance
        order_item = orderItem.objects.create(order=self.order, product=self.product, quantity=1)
        # Reset the mock call count to ignore the initial call during creation
        mock_update_total.reset_mock()
        # Delete the orderItem and check if update_total is called
        order_item.delete()
        self.assertTrue(mock_update_total.called)
        self.assertEqual(mock_update_total.call_count, 1)

# WEBHOOK_HANDLER.PY

# Testing WH_Handler

class WH_Handler:
    """ Handles Stripe Webhooks """
    def __init__(self, request):
        self.request = request

    def handle_payment_succeeded(self, event):
        """ Handle successful payment webhook from Stripe """
        # Retrieve the Stripe event object
        stripe_event = stripe.Event.construct_from(
            event, stripe.api_key
        )

        # Access the necessary data from the Stripe event
        stripe_data = stripe_event.data.object

        # Example: Extract necessary information from stripe_data
        order_id = stripe_data.get('metadata', {}).get('order_id')
        amount = stripe_data.get('amount')
        currency = stripe_data.get('currency')
        email = stripe_data.get('billing_details', {}).get('email')

        # Example: Fetch Order object based on order_id
        order = Order.objects.get(id=order_id)

        # Example: Update order status or perform other actions
        order.status = 'paid'
        order.save()

        # Example: Send confirmation email
        self._confirmation_email(order)

        # Return a response (optional)
        return HttpResponse(status=200)

    def _confirmation_email(self, order):
        """ Sends the user a confirmation email """
        shopper_email = order.email
        subject = render_to_string(
            'checkout/confirmation_email/email_subject.txt',
            {'order': order}
        )

        body = render_to_string(
            'checkout/confirmation_email/email_body.txt',
            {'order': order, 'company_email': settings.DEFAULT_FROM_EMAIL}
        )

        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [shopper_email]
        )


    def setUp(self):
        self.handler = WH_Handler(HttpRequest())

    def test_handle_events_payment_intent_succeeded(self):
        event = {'type': 'payment_intent.succeeded'}
        response = self.handler.handle_events(event)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Unhandled Webhook received: payment_intent.succeeded', response.content.decode('utf-8'))

    def test_handle_events_payment_intent_failed(self):
        event = {'type': 'payment_intent.failed'}
        response = self.handler.handle_events(event)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Unhandled Webhook received: payment_intent.failed', response.content.decode('utf-8'))

    def test_handle_events_unknown_event(self):
        event = {'type': 'unknown_event_type'}
        response = self.handler.handle_events(event)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Unhandled Webhook received: unknown_event_type', response.content.decode('utf-8'))

    def test_handle_payment_succeeded_existing_order(self):
        # Mock event data simulating payment_intent.succeeded event
        event = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "mock_intent_id",
                    "metadata": {
                        "username": "testuser",
                        "shoppingbag": json.dumps({"1": 2})  # Example shopping bag JSON
                    },
                    "shipping": {
                        "name": "John Doe",
                        "phone": "1234567890",
                        "address": {
                            "country": "US",
                            "postal_code": "12345",
                            "city": "New York",
                            "line1": "123 Street",
                            "line2": "Apt 1",
                            "state": "NY"
                        }
                    }
                }
            }
        }

        # Mock UserP object
        with mock.patch('checkout.models.UserP.objects.get') as mock_get_user:
            mock_user = mock.Mock()
            mock_user.default_phone = "1234567890"
            mock_user.default_country = "US"
            mock_user.default_postcode = "12345"
            mock_user.default_city = "New York"
            mock_user.default_address_1 = "123 Street"
            mock_user.default_address_2 = "Apt 1"
            mock_user.default_county = "NY"
            mock_get_user.return_value = mock_user

            # Mock Order object
            with mock.patch('checkout.models.Order.objects.get') as mock_get_order:
                mock_order = mock.Mock()
                mock_get_order.return_value = mock_order

                # Invoke the method
                response = self.handler.handle_payment_succeeded(event)

                # Assertions
                self.assertEqual(response.status_code, 200)
                self.assertIn('Webhook received: payment_intent.succeeded | Success: Verified order already in database', response.content.decode('utf-8'))
                self.assertTrue(mock_get_user.called)
                self.assertTrue(mock_get_order.called)

    def test_handle_payment_succeeded_new_order(self):
        # Mock event data simulating payment_intent.succeeded event for a new order
        event = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "mock_intent_id",
                    "metadata": {
                        "username": "testuser",
                        "shoppingbag": json.dumps({"1": 2})  # Example shopping bag JSON
                    },
                    "shipping": {
                        "name": "John Doe",
                        "phone": "1234567890",
                        "address": {
                            "country": "US",
                            "postal_code": "12345",
                            "city": "New York",
                            "line1": "123 Street",
                            "line2": "Apt 1",
                            "state": "NY"
                        }
                    }
                }
            }
        }

        # Mock Order creation
        with mock.patch('checkout.models.Order.objects.create') as mock_create_order:
            mock_order = mock.Mock()
            mock_create_order.return_value = mock_order

            # Invoke the method
            response = self.handler.handle_payment_succeeded(event)

            # Assertions
            self.assertEqual(response.status_code, 200)
            self.assertIn('Webhook received: payment_intent.succeeded | Success: Created order in webhook', response.content.decode('utf-8'))
            self.assertTrue(mock_create_order.called)

    def test_handle_payment_succeeded_exception_handling(self):
        # Mock event data simulating payment_intent.succeeded event with an exception during Order creation
        event = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "mock_intent_id",
                    "metadata": {
                        "username": "testuser",
                        "shoppingbag": json.dumps({"1": 2})  # Example shopping bag JSON
                    },
                    "shipping": {
                        "name": "John Doe",
                        "phone": "1234567890",
                        "address": {
                            "country": "US",
                            "postal_code": "12345",
                            "city": "New York",
                            "line1": "123 Street",
                            "line2": "Apt 1",
                            "state": "NY"
                        }
                    }
                }
            }
        }

        # Mock Order creation with exception
        with mock.patch('checkout.models.Order.objects.create') as mock_create_order:
            mock_create_order.side_effect = Exception("Test exception")

            # Invoke the method
            response = self.handler.handle_payment_succeeded(event)

            # Assertions
            self.assertEqual(response.status_code, 500)
            self.assertIn('Webhook received: payment_intent.succeeded | ERROR:', response.content.decode('utf-8'))
            self.assertTrue(mock_create_order.called)

    def tearDown(self):
        # Clean up any resources after each test if needed
        pass

    def test_handle_payment_failed(self):
        # Mock event data simulating payment_intent.failed event
        event = {
            "type": "payment_intent.failed",
            "data": {
                "object": {
                    "id": "mock_intent_id",
                    "metadata": {
                        "username": "testuser",
                        "shoppingbag": json.dumps({"1": 2})  # Example shopping bag JSON
                    }
                }
            }
        }

        # Invoke the method
        response = self.handler.handle_payment_failed(event)

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertIn('Payment Failed Webhook received: payment_intent.failed', response.content.decode('utf-8'))

    def tearDown(self):
        # Clean up any resources after each test if needed
        pass

# WEBHOOKS.PY

# Testing webhook

class WH_Handler:
    def __init__(self, request):
        self.request = request

    def handle_payment_succeeded(self, event):
        """
        Handle payment_intent.succeeded event from Stripe webhook.
        """
        try:
            intent_id = event['data']['object']['id']
            # Access other necessary attributes as needed
            # Process the successful payment event here
            # Example: Update order status, send email to customer, etc.
            return HttpResponse(status=200)
        except KeyError as e:
            # Handle missing key in event data
            return HttpResponse(content=f'Missing key in event data: {e}', status=400)
        except Exception as e:
            # Handle other exceptions gracefully
            return HttpResponse(content=str(e), status=400)

    def handle_payment_failed(self, event):
        """
        Handle payment_intent.payment_failed event from Stripe webhook.
        """
        try:
            intent_id = event['data']['object']['id']
            # Access other necessary attributes as needed
            # Process the payment failure event here
            # Example: Notify admin, log error, etc.
            return HttpResponse(status=200)
        except KeyError as e:
            # Handle missing key in event data
            return HttpResponse(content=f'Missing key in event data: {e}', status=400)
        except Exception as e:
            # Handle other exceptions gracefully
            return HttpResponse(content=str(e), status=400)

    def handle_events(self, event):
        """
        Default handler for events not explicitly handled.
        """
        return HttpResponse(content=f'Unhandled event type: {event["type"]}', status=400)

# URLS.PY

# Testing urls.py 

class TestCheckoutUrls(TestCase):

    def test_checkout_url(self):
        url = reverse('checkout')
        self.assertEqual(resolve(url).func, views.checkout)

    def test_checkout_win_url(self):
        order_number = '12345'  # Replace with an actual order number for testing
        url = reverse('checkout_win', args=[order_number])
        self.assertEqual(resolve(url).func, views.checkout_win)

    def test_cache_checkout_data_url(self):
        url = reverse('cache_checkout_data')
        self.assertEqual(resolve(url).func, views.cache_checkout_data)


# ADMIN.PY

class TestOrderAdmin(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('admin', 'admin@example.com', 'admin')
        self.client = Client()
        self.client.force_login(self.user)

    def test_admin_change_order_view(self):
        # Create a test Order with appropriate fields
        order = Order.objects.create(order_number='123', date='2024-01-01', delivery=100.0,  # Example of a decimal value
                                     order_total=100, grand_total=100, OG_shoppingbag='Test',
                                     stripe_pid='pid_test')

        url = reverse('admin:checkout_order_change', args=[order.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Change order')
