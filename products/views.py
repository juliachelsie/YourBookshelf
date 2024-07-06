from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.db.models.functions import Lower
from .models import Product, Category
from .forms import pForm


def every_product(request):
    """ View that shows all products """

    products = Product.objects.all()
    query = None
    categories = None
    sort = None
    direction = None

    if request.GET:
        if 'sort' in request.GET:
            sortkey = request.GET['sort']
            sort = sortkey
            if sortkey == 'name':
                sortkey = 'lower_name'
                products = products.annotate(lower_name=Lower('name'))
            if sortkey == 'category':
                sortkey = 'category__name'
            if 'direction' in request.GET:
                direction = request.GET['direction']
                if direction == 'desc':
                    sortkey = f'-{sortkey}'
            products = products.order_by(sortkey)

        if 'category' in request.GET:
            categories = request.GET['category'].split(',')
            products = products.filter(category__name__in=categories)
            categories = Category.objects.filter(name__in=categories)

        if 'q' in request.GET:
            query = request.GET['q']
            if not query:
                messages.error(request, "You did not search for anything")
                return redirect(reverse('products'))
            
            queries = Q(name__icontains=query) | Q(description__icontains=query) |Q(writer__icontains=query)
            products = products.filter(queries)

    present_sorting = f'{sort}_{direction}'

    context = {
        'products': products,
        'search_term': query,
        'present_categories': categories,
        'present_sorting': present_sorting,
    }
    return render(request, 'products/products.html', context)


def product_info(request, product_id):
    """ View to show one specified product and information"""

    product = get_object_or_404(Product, pk=product_id)
    context = {
        'product': product,
    }
    return render(request, 'products/product_info.html', context)

@login_required
def admin_add_product(request):
    """ Lets Admin add a product to the store """
    if not request.user.is_superuser:
        messages.error(request, 'Sorry, you do not authority to do that.')
        return redirect(reverse('home'))

    if request.method == 'POST':
        form = pForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, 'Product added!')
            return redirect(reverse('product_info', args=[product.id]))
        else:
            messages.error(request, 'Could not add product, Please try again.')
    else:
        form = pForm()

    template = 'products/add_product_bag.html'
    context = {
        'form': form,
    }

    return render(request, template, context)

@login_required
def modify_product(request, product_id):
    """ Modify a product """
    if not request.user.is_superuser:
        messages.error(request, 'Sorry, you do not authority to do that.')
        return redirect(reverse('home'))

    product = get_object_or_404(Product, pk=product_id)
    if request.method == 'POST':
        form = pForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'The product was successfully updated!')
            return redirect(reverse('product_info', args=[product.id]))
        else:
            messages.error(request, 'Could not update product, PLease try again.')
    else:        
        form = pForm(instance=product)
        messages.info(request, f'You are changing {product.name}.')

    template = 'products/modify_product.html'
    context = {
        'form': form,
        'product': product,
    }
        
    return render(request, template, context)

@login_required
def remove_product(request, product_id):
    """ Remove a product """
    if not request.user.is_superuser:
        messages.error(request, 'Sorry, you do not have authority to do that.')
        return redirect(reverse('home'))

    product = get_object_or_404(Product, pk=product_id)
    product.delete()
    messages.success(request, 'Product successfully removed!')
    return redirect(reverse('products'))
