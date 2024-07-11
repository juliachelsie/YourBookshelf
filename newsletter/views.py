from django.shortcuts import render
from django.contrib import messages
from .forms import ContactForm


def contact_view(request):
    if request.method == 'POST':
        contactform = ContactForm(data=request.POST)
        if contactform.is_valid():
            contactform.save()
            messages.success(request, 'Message Sent!')
            return render(request, 'home/index.html')
    contactform = ContactForm()
    template = 'newsletter/newsletter.html'
    context = {'contactform': contactform}
    return render(request, template, context)
