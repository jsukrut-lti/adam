from django.db import models

# Create your models here.

address_type_choice = (
    ('billing', 'Billing'), ('shipping', 'Shipping'),
    ('office', 'Office'), ('personal', 'Personal'),
    ('Other', 'Other'), ('current', 'Current'),
    ('permanent', 'Permanent')
)


class Address(models.Model):
    address_title = models.CharField(max_length=40)
    address_type = models.CharField(max_length=40,
                                    choices=address_type_choice, null=True)
    address_line1 = models.CharField(max_length=100)
    address_line2 = models.CharField(max_length=100)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=50)
    latitude = models.CharField(max_length=50)
    longitude = models.CharField(max_length=50)
    enable = models.BooleanField(default=True)

    def __str__(self):
        return str(self.address_title)
