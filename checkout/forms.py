from django import forms
from .models import Order

class orderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ('first_name', 'last_name', 'email', 'phone',
                 'country', 'address_1', 'address_2', 'city',
                 'postcode', 'county',)

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        placeholders = {
            'first_name' : 'First Name',
            'last_name' : 'Last Name',
            'email' : 'Email Address',
            'phone' : 'Phone number',
            'address_1' : 'Address 1',
            'address_2' : 'Address 2',
            'postcode' : 'Postal Code',
            'city' : 'City',
            'county' : 'County or state',
            'country': 'Country',
        }

        self.fields['first_name'].widget.attrs['autofocus'] = True
        for field in self.fields:
            if self.fields[field].required:
                placeholder = f'{placeholders[field]} *'
            else:
                placeholder = placeholders[field]
            self.fields[field].widget.attrs['placeholder'] = placeholder
            self.fields[field].widget.attrs['class'] = 'stripe-style-input'
            self.fields[field].label = False
        