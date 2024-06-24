from django.shortcuts import render, redirect, reverse, HttpResponse


def view_shoppingbag(request):
    """ A view that renders the shoppingbag contents """

    return render(request, 'shoppingbag/shoppingbag.html')


def add_to_shoppingbag(request, item_id):
    """ Add a quantity of a product to the shoppingbag """

    quantity = int(request.POST.get('quantity'))
    redirect_url = request.POST.get('redirect_url')
    size = None
    if 'p_size' in request.POST:
        size = request.POST['p_size']    
    shoppingbag = request.session.get('shoppingbag', {})

    if size:
        if item_id in list(shoppingbag.keys()):
            if size in shoppingbag[item_id]['items_by_size'].keys():
                shoppingbag[item_id]['items_by_size'][size] += quantity
            else:
                shoppingbag[item_id]['items_by_size'][size] = quantity
        else:
            shoppingbag[item_id] = {'items_by_size' : {size: quantity}}
    else:
        if item_id in list(shoppingbag.keys()):
            shoppingbag[item_id] += quantity
        else:
            shoppingbag[item_id] = quantity
    
    request.session['shoppingbag'] = shoppingbag
    return redirect(redirect_url)


def modify_shoppingbag(request, item_id):
    """ Modify the quantity of a product in the shoppingbag """

    quantity = int(request.POST.get('quantity'))
    size = None
    if 'p_size' in request.POST:
        size = request.POST['p_size']    
    shoppingbag = request.session.get('shoppingbag', {})

    if size:
        if quantity > 0:
            shoppingbag[item_id]['items_by_size'][size] = quantity
        else:
            del shoppingbag[item_id]['items_by_size'][size]
            if not shoppingbag[item_id]['items_by_size'][size]:
                shoppingbag.pop(item_id)
    else:
        if quantity > 0:
            shoppingbag[item_id] = quantity
        else:
            shoppingbag.pop(item_id)
    
    request.session['shoppingbag'] = shoppingbag
    return redirect(reverse('view_shoppingbag'))


def remove_from_shoppingbag(request, item_id):
    """ Remove the quantity of a product from the shoppingbag """
    try:
        size = None
        if 'p_size' in request.POST:
            size = request.POST['p_size']    
        shoppingbag = request.session.get('shoppingbag', {})

        if size:
                del shoppingbag[item_id]['items_by_size'][size]
                if not shoppingbag[item_id]['items_by_size'][size]:
                    shoppingbag.pop(item_id)
        else:
            shoppingbag.pop(item_id)
        
        request.session['shoppingbag'] = shoppingbag
        return HttpResponse(status=200)
    except Exception as e:
        return HttpResponse(status=500)