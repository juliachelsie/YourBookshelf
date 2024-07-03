from decimal import Decimal
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.messages.storage.fallback import FallbackStorage
from unittest.mock import patch, Mock
from products.models import Product
from shoppingbag.contexts import shoppingbag_contents  
from shoppingbag.views import view_shoppingbag, add_to_shoppingbag, modify_shoppingbag, remove_from_shoppingbag

## Testing "shoppingbag_contents" in contexts.py

class ShoppingBagContentsTests(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.product1 = Product.objects.create(name='Test Product 1', price=Decimal('10.00'))
        self.product2 = Product.objects.create(name='Test Product 2', price=Decimal('20.00'))
        settings.FREE_DELIVERY_THRESHOLD = 50
        settings.STANDARD_DELIVERY_PERCENTAGE = 10

    @patch('django.shortcuts.get_object_or_404')
    def test_shoppingbag_contents_with_simple_items(self, mock_get_object_or_404):
        mock_get_object_or_404.side_effect = lambda model, pk: self.product1 if pk == self.product1.pk else self.product2

        request = self.factory.get('/')
        request.session = {'shoppingbag': {str(self.product1.pk): 2, str(self.product2.pk): 1}}

        context = shoppingbag_contents(request)

        self.assertEqual(context['total'], Decimal('40.00'))
        self.assertEqual(context['product_count'], 3)
        self.assertEqual(len(context['shoppingbag_items']), 2)
        self.assertAlmostEqual(context['delivery'], Decimal('4.00'), places=2)
        self.assertAlmostEqual(context['free_delivery_delta'], Decimal('10.00'), places=2)
        self.assertAlmostEqual(context['grand_total'], Decimal('44.00'), places=2)

    @patch('django.shortcuts.get_object_or_404')
    def test_shoppingbag_contents_with_items_by_size(self, mock_get_object_or_404):
        mock_get_object_or_404.side_effect = lambda model, pk: self.product1 if pk == self.product1.pk else self.product2

        request = self.factory.get('/')
        request.session = {'shoppingbag': {str(self.product1.pk): {'items_by_size': {'small': 1, 'large': 2}}, str(self.product2.pk): 1}}

        context = shoppingbag_contents(request)

        self.assertEqual(context['total'], Decimal('50.00'))
        self.assertEqual(context['product_count'], 4)
        self.assertEqual(len(context['shoppingbag_items']), 3)  # One for product2 and two for sizes of product1
        self.assertAlmostEqual(context['delivery'], Decimal('0.00'), places=2)
        self.assertAlmostEqual(context['free_delivery_delta'], Decimal('0.00'), places=2)
        self.assertAlmostEqual(context['grand_total'], Decimal('50.00'), places=2)


## Testing "view_shoppingbag" in views.py.

class ViewShoppingBagTests(TestCase):

    def test_view_shoppingbag(self):
        response = self.client.get(reverse('view_shoppingbag'))  # Adjust URL name if necessary
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'shoppingbag/shoppingbag.html')

# Testing "Add_to_shoppingbag" in views.py

def test_add_to_shoppingbag_with_size(self):
    request = self.factory.post(reverse('add_to_shoppingbag', args=[self.item_id]), {
        'quantity': 1,
        'redirect_url': self.redirect_url,
        'p_size': 'small',  # Example size
    })
    request.session = {}
    request.session['shoppingbag'] = {}
    
    # Add message support to request
    setattr(request, '_messages', FallbackStorage(request))

    response = add_to_shoppingbag(request, self.item_id)
    
    self.assertEqual(response.status_code, 302)  # Check if redirected

    # Check session changes
    shoppingbag = request.session.get('shoppingbag', {})
    self.assertIn(str(self.item_id), shoppingbag)
    self.assertIn('items_by_size', shoppingbag[str(self.item_id)])
    self.assertEqual(shoppingbag[str(self.item_id)]['items_by_size']['small'], 1)  # Check size and quantity
    
    # Check messages
    self.assertEqual(len(messages.get_messages(request)), 1)
    message = list(messages.get_messages(request))[0]
    self.assertEqual(message.message, f'Added size SMALL {self.product.name} to Your shoppingbag!')

# Testing "modify_shoppingbag" in views.py.

def test_modify_shoppingbag_update_quantity(self):
    request = self.factory.post(reverse('modify_shoppingbag', args=[self.item_id]), {
        'quantity': 3,
    })
    request.session = {}
    request.session['shoppingbag'] = {str(self.item_id): 1}
    
    # Add message support to request
    setattr(request, '_messages', FallbackStorage(request))

    response = modify_shoppingbag(request, self.item_id)
    
    self.assertEqual(response.status_code, 302)  # Check if redirected

    # Check session changes
    shoppingbag = request.session.get('shoppingbag', {})
    self.assertIn(str(self.item_id), shoppingbag)
    self.assertEqual(shoppingbag[str(self.item_id)], 4)  # Check updated quantity
    
    # Check messages
    self.assertEqual(len(messages.get_messages(request)), 1)
    message = list(messages.get_messages(request))[0]
    self.assertEqual(message.message, f'Updated {self.product.name} quantity to 4')

# Testing "remove_from_shoppingbag" from views.py.

def remove_from_shoppingbag(request, item_id):
    """ Remove the quantity of a product from the shoppingbag """
    try:
        product = get_object_or_404(Product, pk=item_id)
        size = request.POST.get('p_size') if 'p_size' in request.POST else None
        shoppingbag = request.session.get('shoppingbag', {})

        if size:
            if item_id in shoppingbag and size in shoppingbag[item_id]['items_by_size']:
                del shoppingbag[item_id]['items_by_size'][size]
                if not shoppingbag[item_id]['items_by_size']:  # Check if no more sizes for this item
                    shoppingbag.pop(item_id)
                return JsonResponse({'message': f'Removed size {size.upper()} {product.name} from Your shoppingbag'}, status=200)
            else:
                raise ValueError('Item or size not found in shoppingbag.')
        else:
            if item_id in shoppingbag:
                shoppingbag.pop(item_id)
                return JsonResponse({'message': f'Removed {product.name} from Your shoppingbag'}, status=200)
            else:
                raise ValueError('Item not found in shoppingbag.')

    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)
    except ValueError as ve:
        return JsonResponse({'error': str(ve)}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error removing item: {e}'}, status=500)