from django.test import TestCase, RequestFactory, Client
from django.contrib.auth.models import User
from django import forms
from unittest.mock import patch
from django.urls import reverse, resolve
from django.shortcuts import get_object_or_404, render
from django.http import Http404, HttpRequest
from django.template.loader import render_to_string
from django.contrib.messages.storage.fallback import FallbackStorage
from django_countries import countries
from django.contrib.messages import get_messages
from django.db.models.signals import post_save
from django.core.exceptions import ObjectDoesNotExist

from . import views
from .views import o_history
from .forms import ProfileForm
from profiles.models import UserP, create_update_profile
from profiles.views import user_profile
from profiles.forms import ProfileForm
from checkout.models import Order

# MODELS.PY

# Testing "UserP" from models.py

class UserPModelTests(TestCase):

    def setUp(self):
        # Create a User object for testing
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123'
        )

    def test_userp_creation(self):
        # Check if a UserP instance already exists for self.user
        if not UserP.objects.filter(user=self.user).exists():
            # Create a UserP object linked to self.user
            user_profile = UserP.objects.create(
                user=self.user,
                default_first_name='Test',
                default_last_name='User',
                default_phone='123-456-7890',
                default_email='testuser@example.com',
                default_address_1='456 Oak St',
                default_city='Sometown',
                default_country=countries.alpha2('US'),
                default_postcode='54321',
            )

            # Query the database to check if the UserP object exists
            saved_user_profile = UserP.objects.get(user=self.user)
            
            # Assert that the saved UserP instance matches the created instance
            self.assertEqual(saved_user_profile.default_first_name, 'Test')
            # Add other assertions for other fields as needed

        else:
            # UserP instance already exists, handle appropriately (optional)
            pass

    def test_userp_str_method(self):
        # Create a UserP object linked to self.user
        if not UserP.objects.filter(user=self.user).exists():
            user_profile = UserP.objects.create(
                user=self.user,
                default_first_name='Test',
                default_last_name='User',
                default_phone='123-456-7890',
                default_email='testuser@example.com',
                default_address_1='456 Oak St',
                default_city='Sometown',
                default_country=countries.alpha2('US'),
                default_postcode='54321',
            )

            # Check the string representation of the UserP instance
            self.assertEqual(str(user_profile), 'testuser')

        else:
            # UserP instance already exists, handle appropriately (optional)
            pass

# Testing "create_update_profile" from models.py
class UserPProfileCreationTest(TestCase):

    def setUp(self):
        # Ensure the signal is connected before each test
        post_save.connect(create_update_profile, sender=User)

    def tearDown(self):
        # Disconnect the signal after each test to avoid interference
        post_save.disconnect(create_update_profile, sender=User)

    def test_create_user_creates_userp(self):
        # Create a new User instance
        user = User.objects.create_user(username='testuser', password='password123')

        # Check if UserP instance was created
        try:
            userp_profile = UserP.objects.get(user=user)
        except ObjectDoesNotExist:
            self.fail("UserP profile was not created for the user.")

        # Assert that the UserP instance exists and is associated with the user
        self.assertEqual(userp_profile.user, user)

    def test_update_user_updates_userp(self):
        # Create a new User instance
        user = User.objects.create_user(username='testuser', password='password123')

        # Retrieve the UserP instance
        userp_profile = UserP.objects.get(user=user)

        # Modify the user's username (triggering an update)
        user.username = 'updated_username'
        user.save()

        # Refresh the UserP instance from the database
        userp_profile.refresh_from_db()

        # Assert that the UserP instance has been updated
        self.assertEqual(userp_profile.user.username, 'updated_username')

    def test_signal_disconnection(self):
        # Disconnect the signal temporarily for this test
        post_save.disconnect(create_update_profile, sender=User)

        # Create a new User instance
        user = User.objects.create_user(username='testuser', password='password123')

        # Check if UserP instance was NOT created
        with self.assertRaises(ObjectDoesNotExist):
            UserP.objects.get(user=user)

        # Reconnect the signal for subsequent tests
        post_save.connect(create_update_profile, sender=User)


# VIEWS.PY

# Testing "user_profile" from views.py

class UserProfileViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        self.userp = UserP.objects.create(user=self.user)  # Create UserP object for the user

    def test_user_profile_view_get(self):
        self.client.force_login(self.user)  # Simulate logged in user

        # Make a GET request to the user_profile view
        response = self.client.get(reverse('user_profile'))

        # Check if the response is OK (status code 200)
        self.assertEqual(response.status_code, 200)

        # Check if 'orders' and 'form' are in the response context
        self.assertIn('orders', response.context)
        self.assertIn('form', response.context)
        self.assertTrue(response.context['profilePage'])

# Testing "o_history" from views.py

class OrderHistoryViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.order_number = '123456789'  # Replace with an existing order number in your system
        self.order = Order.objects.create(order_number=self.order_number)
        self.url = reverse('o_history', kwargs={'order_number': self.order_number})

    def test_o_history_view_with_valid_order_number(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'checkout/checkout_win.html')
        self.assertEqual(response.context['order'].order_number, self.order_number)
        self.assertTrue(response.context['profile_history_form'])

        messages = [str(msg) for msg in get_messages(response.wsgi_request)]
        expected_message = f'This is a old confirmation for order number {self.order_number}, A confirmation email was sent to You on the order date.'
        self.assertIn(expected_message, messages)

    def test_o_history_view_with_invalid_order_number(self):
        self.client.login(username='testuser', password='12345')
        invalid_order_number = 'invalid_order_number'
        invalid_url = reverse('o_history', kwargs={'order_number': invalid_order_number})

        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, 404)

    def test_o_history_view_redirects_when_not_logged_in(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/accounts/login/?next={self.url}')

    def test_o_history_view_does_not_set_message_when_not_logged_in(self):
        request = self.client.get(self.url)
        messages = [str(msg) for msg in get_messages(request.wsgi_request)]
        self.assertNotIn('This is an old confirmation', messages)

# FORMS.PY

# Testing "ProfileForm" in forms.py

class ProfileFormTest(TestCase):

    def test_form_valid_data(self):
        valid_country_code = 'US'  # Assuming 'US' is a valid choice

        form = ProfileForm(data={
            'default_first_name': 'John',
            'default_last_name': 'Doe',
            'default_email': 'john.doe@example.com',
            'default_phone': '1234567890',
            'default_address_1': '123 Main St',
            'default_address_2': '',
            'default_postcode': '12345',
            'default_city': 'Anytown',
            'default_county': 'Anycounty',
            'default_country': valid_country_code,
        })
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

    def test_form_empty_required_fields(self):
        form = ProfileForm(data={})
        self.assertFalse(form.is_valid(), "The form should be invalid when required fields are empty")

        required_fields = [
            'default_first_name', 'default_last_name', 'default_email',
            'default_phone', 'default_address_1', 'default_postcode',
            'default_city', 'default_county', 'default_country'
        ]
        
        for field in required_fields:
            self.assertIn(field, form.errors, f"{field} should be in form errors")
            
    def test_form_invalid_country(self):
        invalid_country_code = 'INVALID'

        form = ProfileForm(data={
            'default_first_name': 'John',
            'default_last_name': 'Doe',
            'default_email': 'john.doe@example.com',
            'default_phone': '1234567890',
            'default_address_1': '123 Main St',
            'default_address_2': '',
            'default_postcode': '12345',
            'default_city': 'Anytown',
            'default_county': 'Anycounty',
            'default_country': invalid_country_code,
        })
        self.assertFalse(form.is_valid(), "The form should be invalid with an invalid country code")
        self.assertIn('default_country', form.errors, "default_country should be in form errors")

# URLS.PY

# Testing urls.py 

class UrlsTestCase(TestCase):
    def setUp(self):
        # Create a test user if needed
        self.user = User.objects.create_user(username='testuser', password='12345')

    def test_user_profile_url(self):
        url = reverse('user_profile')
        self.assertEqual(resolve(url).func, views.user_profile)

    def test_user_profile_view(self):
        self.client.force_login(self.user)  # Log in the client
        url = reverse('user_profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
