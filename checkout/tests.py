from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.shortcuts import get_object_or_404
from unittest.mock import patch, MagicMock, Mock

from checkout.views import checkout, checkout_win
from checkout.models import orderItem, Order
from checkout.forms import orderForm
from profiles.forms import ProfileForm
from products.models import Product


# Unittest for checkout in views.py

class CheckoutViewTests(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', password='testpassword')

    def test_checkout_view_get_empty_shopping_bag(self):
        request = self.factory.get(reverse('checkout'))
        request.session = {'shoppingbag': {}}  # Empty shopping bag

        # Set up messages framework
        setattr(request, '_messages', Mock())

        response = checkout(request)

        self.assertEqual(response.status_code, 302)  # Expecting a redirect

        # Check the redirection target
        self.assertEqual(response.url, reverse('products'))


# Unittest for checkout_win in views.py

