from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import ProfileForm
from .models import UserP
from checkout.models import Order


@login_required
def user_profile(request):
    """ Display the profile """
    user_profile = get_object_or_404(UserP, user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated!')
    else:
        messages.error(request, 'Could not update profile, Please try again!')

    form = ProfileForm(instance=user_profile)
    orders = user_profile.orders.all()

    template = 'profiles/profile.html'
    context = {
        'orders': orders,
        'form': form,
        'profilePage': True
        
    }

    return render(request, template, context)


def o_history(request, order_number):
    order =get_object_or_404(Order, order_number=order_number)

    messages.info(request, (
        f'This is a old confirmation for order number {order_number}, '
        'A confirmation email was sent to You on the order date.'
    ))

    template = 'checkout/checkout_win.html'
    context = {
        'order': order,
        'profile_history_form': True,
    }

    return render(request, template, context)

