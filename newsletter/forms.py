from .models import Contact
from django import forms
from django.forms import ModelForm

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['first_name', 'last_name', 'phone', 'email']