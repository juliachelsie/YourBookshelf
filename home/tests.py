from django.test import TestCase
from django.shortcuts import render
from django.urls import reverse

# VIEWS.PY

# Testing "index" from views.py

class IndexViewTests(TestCase):

    def test_index_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/index.html')


# URLS.PY

# Testing urls.py
class IndexViewTests(TestCase):

    def test_index_view(self):
        url = reverse('home')  # Get the URL for 'home' name
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)  # Check that the response is OK
        self.assertTemplateUsed(response, 'home/index.html')  # Check that index.html template is used


