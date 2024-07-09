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
        required_fields = ['default_first_name', 'default_last_name', 'default_email', 'default_phone', 'default_address_1', 'default_postcode', 'default_city', 'default_county', 'default_country']
        
        for field in self.fields:
            if field in required_fields:
                self.fields[field].required = True
                placeholder = f'{placeholders[field]} *'
            else:
                self.fields[field].required = False
                placeholder = placeholders[field]
            self.fields[field].widget.attrs['placeholder'] = placeholder
            self.fields[field].widget.attrs['class'] = 'rounded-2 profile-form'
            self.fields[field].label = False
        