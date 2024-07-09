from django.test import TestCase, RequestFactory, Client
from django.urls import reverse, resolve
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.functions import Lower
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.contrib import messages
from django.contrib.admin.sites import AdminSite
from django.contrib.messages import get_messages
from django.shortcuts import redirect
from django.db.models import Q

from . import views
from .forms import pForm
from .views import admin_add_product
from products.models import Product, Category
from products.views import every_product
from .models import Product, Category
from .admin import ProductAdmin, CategoryAdmin


# VIEWS.PY

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

# Testing "admin_add_product" from views.py.

class AdminAddProductViewTest(TestCase):

    def setUp(self):
        # Create a superuser for testing
        self.user = User.objects.create_superuser(username='admin', email='admin@example.com', password='password')

    def test_admin_add_product_get_request(self):
        # Simulate a GET request to admin_add_product
        self.client.force_login(self.user)  # Login the user
        response = self.client.get(reverse('admin_add_product'))  # Replace with your URL name
        self.assertEqual(response.status_code, 200)  # Ensure response is successful

    def test_admin_add_product_not_superuser(self):
        # Simulate access for a non-superuser
        non_superuser = User.objects.create_user(username='user', password='password')
        self.client.force_login(non_superuser)  # Login the non-superuser
        response = self.client.get(reverse('admin_add_product'))  # Replace with your URL name
        self.assertEqual(response.status_code, 302)  # Ensure non-superuser is redirected

# Testing "modify_product" from views.py

class ModifyProductViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser(username='admin', email='admin@example.com', password='password')
        self.client = Client()

    def test_post_valid_form(self):
        self.client.force_login(self.user)
        product = Product.objects.create(name='Test Product', price=100)
        product_id = product.id
        form_data = {
            'name': 'Updated Product',
            'description': 'Updated description for the product.',  # Added required field
            'price': 150,
            'category': '',
            'sku': '',
            'size': 'unknown',
            'writer': '',
            'rating': '',
            'image_url': '',
            'image': '',
        }
        response = self.client.post(reverse('modify_product', args=[product_id]), form_data)

        print("Response status code:", response.status_code)
        print("Response content:", response.content.decode())
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('product_info', args=[product_id]))

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'The product was successfully updated!')

        updated_product = Product.objects.get(id=product_id)
        self.assertEqual(updated_product.name, 'Updated Product')
        self.assertEqual(updated_product.description, 'Updated description for the product.')
        self.assertEqual(updated_product.price, 150)

# Testing "remove_product" from views.py.

class RemoveProductViewTest(TestCase):

    def setUp(self):
        # Create a superuser and a regular user
        self.superuser = User.objects.create_superuser(username='admin', email='admin@example.com', password='password')
        self.user = User.objects.create_user(username='regular', email='regular@example.com', password='password')
        self.client = Client()

        # Create a product
        self.product = Product.objects.create(name='Test Product', price=100)

    def test_remove_product_not_logged_in(self):
        product_id = self.product.id
        url = reverse('remove_product', args=[product_id])
        print(f"Testing URL for not logged in user: {url}")  # Debug statement
        response = self.client.post(url)
        
        print(f"Response status code: {response.status_code}")
        self.assertNotEqual(response.status_code, 200)  # Should redirect to login
        self.assertRedirects(response, f'/accounts/login/?next={url}')

    def test_remove_product_not_superuser(self):
        self.client.login(username='regular', password='password')
        product_id = self.product.id
        url = reverse('remove_product', args=[product_id])
        response = self.client.post(url)
        
        self.assertRedirects(response, reverse('home'))
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Sorry, you do not have authority to do that.')

    def test_remove_product_superuser(self):
        self.client.login(username='admin', password='password')
        product_id = self.product.id
        url = reverse('remove_product', args=[product_id])
        response = self.client.post(url)

        self.assertRedirects(response, reverse('products'))
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Product successfully removed!')

        # Check that the product is actually removed
        with self.assertRaises(Product.DoesNotExist):
            Product.objects.get(pk=product_id)

# MODELS.PY

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

# FORMS.PY

# Testing "pForm" from forms.py.

class pFormTests(TestCase):

    def setUp(self):
        # Set up test data
        self.category1 = Category.objects.create(name='Category 1', friendly_name='Friendly Category 1')
        self.category2 = Category.objects.create(name='Category 2', friendly_name='Friendly Category 2')
        self.product_data = {
            'name': 'Test Product',
            'description': 'Test Description',
            'category': self.category1.id,
            'price': 10.0,
        }

    def test_form_initialization(self):
        form = pForm()
        # Check if the 'category' field choices are populated correctly
        expected_choices = [(self.category1.id, 'Friendly Category 1'), (self.category2.id, 'Friendly Category 2')]
        self.assertEqual(form.fields['category'].choices, expected_choices)

    def test_form_field_attributes(self):
        form = pForm()
        # Check if the widget attributes are set correctly for each field
        for field_name, field in form.fields.items():
            self.assertEqual(field.widget.attrs['class'], 'border-black rounded-2')

    def test_form_valid_data(self):
        form = pForm(data=self.product_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_data(self):
        # Test invalid data (missing required fields, etc.)
        invalid_data = {
            'name': '',
            'description': 'Test Description',
            'price': 10.0,
        }
        form = pForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)  # Ensure 'name' field has errors


# ADMIN.PY 

# Testing "ProductAdmin" from admin.py

class MockRequest:
    pass

class MockSuperUser:
    def has_perm(self, perm):
        return True

class ProductAdminTests(TestCase):

    def setUp(self):
        # Create a superuser for testing
        self.client = Client()
        self.user = User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')
        self.client.force_login(self.user)

        # Set up test data
        self.category = Category.objects.create(name='Test Category', friendly_name='Friendly Category')
        self.product = Product.objects.create(
            sku='TEST001',
            name='Test Product',
            writer='Test Writer',
            category=self.category,
            rating=4.5,
            price=19.99,
            image='product_image.jpg'
        )

    def test_product_admin_list_display(self):
        # Check that list_display matches the expected fields
        expected_list_display = (
            'sku',
            'name',
            'writer',
            'category',
            'rating',
            'price',
            'image',
        )
        admin_instance = ProductAdmin(Product, AdminSite())
        self.assertEqual(admin_instance.list_display, expected_list_display)

    def test_product_admin_ordering(self):
        # Check that ordering matches the expected tuple
        expected_ordering = ('sku',)
        admin_instance = ProductAdmin(Product, AdminSite())
        self.assertEqual(admin_instance.ordering, expected_ordering)

    def test_product_admin_change_view(self):
        # Check that the product admin change view works
        change_url = reverse('admin:products_product_change', args=(self.product.id,))
        response = self.client.get(change_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)

    def test_product_admin_add_view(self):
        # Check that the product admin add view works
        add_url = reverse('admin:products_product_add')
        response = self.client.get(add_url)
        self.assertEqual(response.status_code, 200)

# Testing "CategoryAdmin" from admin.py

class MockRequest:
    pass

class MockSuperUser:
    def has_perm(self, perm):
        return True

class CategoryAdminTests(TestCase):

    def setUp(self):
        # Create a superuser for testing
        self.client = Client()
        self.user = User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')
        self.client.force_login(self.user)

        # Set up test data
        self.category = Category.objects.create(name='Test Category', friendly_name='Friendly Category')

    def test_category_admin_list_display(self):
        # Check that list_display matches the expected fields
        expected_list_display = (
            'friendly_name',
            'name',
        )
        admin_instance = CategoryAdmin(Category, AdminSite())
        self.assertEqual(admin_instance.list_display, expected_list_display)

    def test_category_admin_change_view(self):
        # Check that the category admin change view works
        change_url = reverse('admin:products_category_change', args=(self.category.id,))
        response = self.client.get(change_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.category.name)

    def test_category_admin_add_view(self):
        # Check that the category admin add view works
        add_url = reverse('admin:products_category_add')
        response = self.client.get(add_url)
        self.assertEqual(response.status_code, 200)

    # Add more tests as needed for CategoryAdmin

# URLS.PY

class TestUrls(TestCase):

    def test_products_url_resolves(self):
        url = reverse('products')
        self.assertEqual(resolve(url).func, views.every_product)

    def test_product_info_url_resolves(self):
        url = reverse('product_info', args=[1])  # Assuming product_id=1 for testing
        self.assertEqual(resolve(url).func, views.product_info)

    def test_admin_add_product_url_resolves(self):
        url = reverse('admin_add_product')
        self.assertEqual(resolve(url).func, views.admin_add_product)

    def test_modify_product_url_resolves(self):
        url = reverse('modify_product', args=[1])  # Assuming product_id=1 for testing
        self.assertEqual(resolve(url).func, views.modify_product)

    def test_remove_product_url_resolves(self):
        url = reverse('remove_product', args=[1])  # Assuming product_id=1 for testing
        self.assertEqual(resolve(url).func, views.remove_product)