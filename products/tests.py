from django.test import TestCase, Client
from django.urls import reverse
from .models import Category, Product

# Test for Category in models.py

class CategoryModelTest(TestCase):
    def setUp(self):
        self.category_with_friendly_name = Category.objects.create(
            name="Electronics",
            friendly_name="Gadgets"
        )
        self.category_without_friendly_name = Category.objects.create(
            name="Books"
        )

    def test_string_representation(self):
        category = self.category_with_friendly_name
        self.assertEqual(str(category), "Electronics")

    def test_get_friendly_name(self):
        category_with_friendly_name = self.category_with_friendly_name
        self.assertEqual(category_with_friendly_name.get_friendly_name(), "Gadgets")
        
        category_without_friendly_name = self.category_without_friendly_name
        self.assertEqual(category_without_friendly_name.get_friendly_name(), None)

    def test_create_category_with_name_only(self):
        category = Category.objects.create(name="Music")
        self.assertEqual(category.name, "Music")
        self.assertIsNone(category.friendly_name)
    
    def test_create_category_with_name_and_friendly_name(self):
        category = Category.objects.create(name="Clothing", friendly_name="Apparel")
        self.assertEqual(category.name, "Clothing")
        self.assertEqual(category.friendly_name, "Apparel")

    def test_get_friendly_name_when_blank(self):
        category = Category.objects.create(name="Movies", friendly_name="")
        self.assertEqual(category.get_friendly_name(), "")    


# Test for Product in models.py

class ProductModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Books",
            friendly_name="Books and Novels"
        )
        self.product = Product.objects.create(
            category=self.category,
            sku="12345",
            name="Sample Product",
            writer="Sample Writer",
            description="This is a sample product.",
            rating=4.50,
            price=19.99,
            image_url="http://example.com/image.jpg"
        )

    def test_string_representation(self):
        self.assertEqual(str(self.product), "Sample Product")

    def test_product_category(self):
        self.assertEqual(self.product.category.name, "Books")
        self.assertEqual(self.product.category.friendly_name, "Books and Novels")

    def test_product_sku(self):
        self.assertEqual(self.product.sku, "12345")

    def test_product_name(self):
        self.assertEqual(self.product.name, "Sample Product")

    def test_product_writer(self):
        self.assertEqual(self.product.writer, "Sample Writer")

    def test_product_description(self):
        self.assertEqual(self.product.description, "This is a sample product.")

    def test_product_rating(self):
        self.assertEqual(self.product.rating, 4.50)

    def test_product_price(self):
        self.assertEqual(self.product.price, 19.99)

    def test_product_image_url(self):
        self.assertEqual(self.product.image_url, "http://example.com/image.jpg")

    def test_product_image(self):
        self.assertFalse(bool(self.product.image))  # Check if the image field is not set


# Test for every_product in views.py

class EveryProductViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(
            name="Books",
            friendly_name="Books and Novels"
        )
        self.product1 = Product.objects.create(
            category=self.category,
            sku="12345",
            name="Sample Product 1",
            writer="Sample Writer 1",
            description="This is a sample product 1.",
            rating=4.50,
            price=19.99,
            image_url="http://example.com/image1.jpg"
        )
        self.product2 = Product.objects.create(
            category=self.category,
            sku="67890",
            name="Sample Product 2",
            writer="Sample Writer 2",
            description="This is a sample product 2.",
            rating=4.00,
            price=29.99,
            image_url="http://example.com/image2.jpg"
        )

    def test_products_view(self):
        response = self.client.get(reverse('products'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'products/products.html')
        
        # Get the list of product names from the queryset in the context
        product_names = [product.name for product in response.context['products']]
        
        # Compare the product names with the expected names
        self.assertIn(self.product1.name, product_names)
        self.assertIn(self.product2.name, product_names)
