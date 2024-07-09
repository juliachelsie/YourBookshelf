from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.sessions.middleware import SessionMiddleware
from django.db.models import Sum
from django.http import HttpRequest
from django.conf import settings
from django_countries import countries
from django_countries.fields import Country
from decimal import Decimal, ROUND_HALF_UP
from unittest.mock import patch, Mock
import stripe
import json
import uuid

from .models import Order, orderItem
from .forms import orderForm
from profiles.models import UserP
from profiles.forms import ProfileForm
from products.models import Product


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