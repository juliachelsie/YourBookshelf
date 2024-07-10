from django.test import TestCase, RequestFactory, Client
from django.urls import reverse
from django.contrib import admin
from django.contrib import messages
from django.contrib.admin.sites import site
from django.contrib.messages import get_messages
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import HttpRequest
from django.test import RequestFactory

from .models import Contact
from .views import contact_view
from .forms import ContactForm
from newsletter import views
from .admin import OrderItemAdmin


# FORMS.PY

# Testing ContactForm from forms.py

class TestContactForm(TestCase):

    def test_contact_form_valid(self):
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': '1234567890',
            'email': 'john.doe@example.com'
        }
        form = ContactForm(data=form_data)
        self.assertTrue(form.is_valid())  # Check if the form data is valid

    def test_contact_form_save(self):
        form_data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'phone': '0987654321',
            'email': 'jane.smith@example.com'
        }
        form = ContactForm(data=form_data)
        self.assertTrue(form.is_valid())  # Check if the form data is valid

        contact = form.save()  # Save the form to create a Contact object
        self.assertEqual(contact.first_name, 'Jane')  # Check if the first_name field was saved correctly
        self.assertEqual(contact.last_name, 'Smith')  # Check if the last_name field was saved correctly
        self.assertEqual(contact.phone, '0987654321')  # Check if the phone field was saved correctly
        self.assertEqual(contact.email, 'jane.smith@example.com')  # Check if the email field was saved correctly

# MODELS.PY

# Testing Contact from models.py

class TestContactModel(TestCase):

    def setUp(self):
        self.contact = Contact.objects.create(
            first_name='John',
            last_name='Doe',
            phone='1234567890',
            email='john.doe@example.com'
        )

    def test_contact_creation(self):
        self.assertIsInstance(self.contact, Contact)  # Check if the contact object is an instance of Contact model

    def test_contact_str_method(self):
        self.assertEqual(str(self.contact), 'john.doe@example.com')  # Check if __str__ method returns email correctly

    def test_phone_field_blank(self):
        contact = Contact.objects.create(
            first_name='Jane',
            last_name='Smith',
            email='jane.smith@example.com'
        )
        self.assertIsNone(contact.phone)  # Check if phone field allows null values

    def test_email_field_blank(self):
        contact = Contact.objects.create(
            first_name='Jane',
            last_name='Smith',
            phone='0987654321'
        )
        self.assertIsNone(contact.email)  # Check if email field allows null values

    def test_phone_field_max_length(self):
        max_length = Contact._meta.get_field('phone').max_length
        self.assertEqual(max_length, 20)  # Check if max_length attribute of phone field is correctly set

    def test_email_field_max_length(self):
        max_length = Contact._meta.get_field('email').max_length
        self.assertEqual(max_length, 250)  # Check if max_length attribute of email field is correctly set

# VIEWS.PY

# Testing "contact_view" from views.

class ContactViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_get_request(self):
        url = reverse('newsletter')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'newsletter/newsletter.html')
        self.assertIn('contactform', response.context)
        self.assertIsInstance(response.context['contactform'], ContactForm)

    def test_post_request_valid_form(self):
        url = reverse('contact_view')
        data = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'message': 'Test message'
        }
        response = self.client.post(url, data, follow=True)

        self.assertEqual(response.status_code, 200)

# URLS.PY

# Testing urls.py

class UrlsTestCase(TestCase):
    
    def setUp(self):
        self.client = Client()
    
    def test_newsletter_url_mapping(self):
        response = self.client.get(reverse('newsletter'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'newsletter/newsletter.html')
        self.assertEqual(response.resolver_match.func, views.contact_view)
    
    def test_contact_view_url_mapping(self):
        response = self.client.get(reverse('contact_view'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'newsletter/newsletter.html')
        self.assertEqual(response.resolver_match.func, views.contact_view)

# ADMIN.PY

class OrderItemAdminTest(TestCase):

    def test_order_item_admin_model(self):
        # Ensure the model associated with OrderItemAdmin is Contact
        self.assertEqual(OrderItemAdmin.model, Contact)

    def test_order_item_admin_in_admin_site(self):
        # Check if Contact model is registered with the admin site
        self.assertIn(Contact, admin.site._registry)

        # Retrieve the registered admin instance for Contact
        contact_admin = admin.site._registry[Contact]

