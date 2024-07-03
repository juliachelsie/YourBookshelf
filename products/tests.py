from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.messages.storage.fallback import FallbackStorage
from django.db.models.functions import Lower
from django.http import Http404
from django.shortcuts import redirect
from django.db.models import Q
from products.models import Product, Category
from products.views import every_product
from django.test import Client
from .models import Product, Category

# Testing "every_product" in views.py

class EveryProductViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category1 = Category.objects.create(name='Category 1')
        cls.category2 = Category.objects.create(name='Category 2')

        # Provide a price value for each product creation
        cls.product1 = Product.objects.create(name='Product 1', description='Description 1', writer='Writer 1', category=cls.category1, price=10.00)
        cls.product2 = Product.objects.create(name='Product 2', description='Description 2', writer='Writer 2', category=cls.category2, price=15.00)

    def setUp(self):
        self.factory = RequestFactory()

# Testing product_info in views.py.

class ProductInfoViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create a test product
        cls.product = Product.objects.create(
            name='Test Product',
            description='Test description',
            writer='Test Writer',
            price=19.99,  # Ensure all required fields are provided
        )

    def test_product_info_view(self):
        # Test for a valid product ID
        url = reverse('product_info', kwargs={'product_id': self.product.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'products/product_info.html')
        self.assertEqual(response.context['product'], self.product)

    def test_product_info_invalid_id(self):
        # Test for an invalid product ID
        url = reverse('product_info', kwargs={'product_id': 999})  # Assuming product with ID 999 does not exist
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_product_info_template(self):
        # Test template rendering
        url = reverse('product_info', kwargs={'product_id': self.product.pk})
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'products/product_info.html')

# Testing "Category" from models.py.

class CategoryModelTests(TestCase):

    def setUp(self):
        self.category = Category.objects.create(
            name='Test Category',
            friendly_name='Friendly Test Category'
        )

    def test_category_creation(self):
        self.assertEqual(self.category.name, 'Test Category')
        self.assertEqual(self.category.friendly_name, 'Friendly Test Category')

    def test_category_str_method(self):
        self.assertEqual(str(self.category), 'Test Category')

    def test_category_get_friendly_name(self):
        self.assertEqual(self.category.get_friendly_name(), 'Friendly Test Category')

# Testing "Product" from models.py.

class ProductModelTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create a Category instance
        cls.category = Category.objects.create(
            name='Test Category'
        )

        # Create a Product instance
        cls.product = Product.objects.create(
            category=cls.category,
            sku='PROD123',
            name='Test Product',
            writer='Test Writer',
            description='This is a test product.',
            rating=4.5,
            price=19.99,
            image_url='https://example.com/image.png',
        )

    def test_product_creation(self):
        self.assertEqual(self.product.category, self.category)
        self.assertEqual(self.product.sku, 'PROD123')
        self.assertEqual(self.product.name, 'Test Product')
        self.assertEqual(self.product.writer, 'Test Writer')
        self.assertEqual(self.product.description, 'This is a test product.')
        self.assertEqual(self.product.rating, 4.5)
        self.assertEqual(self.product.price, 19.99)
        self.assertEqual(self.product.image_url, 'https://example.com/image.png')

    def test_product_str_method(self):
        self.assertEqual(str(self.product), 'Test Product')


