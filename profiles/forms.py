from django import forms
from .models import UserP

class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserP
        exclude = ('user',)

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        placeholders = {
            'default_first_name' : 'First Name',
            'default_last_name' : 'Last Name',
            'default_email' : 'Email Address',
            'default_phone' : 'Phone number',
            'default_address_1' : 'Adress 1',
            'default_address_2' : 'Adress 2',
            'default_postcode' : 'Postal Code',
            'default_city' : 'City',
            'default_county' : 'County or state',
            'default_country': 'Country',
        }

        self.fields['default_first_name'].widget.attrs['autofocus'] = True
        for field in self.fields:
            if self.fields[field].required:
                placeholder = f'{placeholders[field]} *'
            else:
                placeholder = placeholders[field]
            self.fields[field].widget.attrs['placeholder'] = placeholder
            self.fields[field].widget.attrs['class'] = 'rounded-2 profile-form'
            self.fields[field].label = False
        