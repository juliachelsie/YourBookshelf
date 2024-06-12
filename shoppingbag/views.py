from django.shortcuts import render, redirect


def view_shoppingbag(request):
    """ A view that renders the shoppingbag contents """

    return render(request, 'shoppingbag/shoppingbag.html')


def add_to_shoppingbag(request, item_id):
    """ Add a quantity of a product to the shoppingbag """

    quantity = int(request.POST.get('quantity'))
    redirect_url = request.POST.get('redirect_url')
    shoppingbag = request.session.get('shoppingbag', {})

    if item_id in list(shoppingbag.keys()):
        shoppingbag[item_id] += quantity
    else:
        shoppingbag[item_id] = quantity
    
    request.session['shoppingbag'] = shoppingbag
    print(request.session['shoppingbag'])
    return redirect(redirect_url)