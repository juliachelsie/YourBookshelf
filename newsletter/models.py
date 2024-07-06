from django.db import models

class Contact(models.Model):
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=False, null=True)
    email = models.EmailField(max_length=250, blank=False, null=True)

    def __str__(self):
        return self.email
