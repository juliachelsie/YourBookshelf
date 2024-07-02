from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from .forms import ProfileForm
from .models import UserP

def user_profile(request):
    """ Display the profile """
    user_profile = get_object_or_404(UserP, user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated!')

    form = ProfileForm(instance=user_profile)
    orders = user_profile.orders.all()

    template = 'profiles/profile.html'
    context = {
        'orders': orders,
        'form': form,
        'profilePage': True
        
    }

    return render(request, template, context)
