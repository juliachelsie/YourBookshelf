from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpRequest
from django.conf import settings
from decimal import Decimal
from unittest.mock import patch
import stripe
import json

from .models import Order, orderItem
from .forms import orderForm
from profiles.models import UserP  
from products.models import Product

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



