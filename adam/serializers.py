from rest_framework import serializers
from .models import PanelMaster


address_type_choice = (
    ('billing', 'Billing'), ('shipping', 'Shipping'),
    ('office', 'Office'), ('personal', 'Personal'),
    ('Other', 'Other'), ('current', 'Current'),
    ('permanent', 'Permanent')
)


class AddressSerializers(serializers.ModelSerializer):
    address_title = serializers.CharField(max_length=40)
    address_type = serializers.ChoiceField(choices=address_type_choice)
    address_line1 = serializers.CharField(max_length=100)
    address_line2 = serializers.CharField(max_length=100)
    city = serializers.CharField(max_length=50)
    state = serializers.CharField(max_length=50)
    country = serializers.CharField(max_length=50)
    postal_code = serializers.CharField(max_length=50)
    latitude = serializers.CharField(max_length=50)
    longitude = serializers.CharField(max_length=50)

    class Meta:
        model = PanelMaster
        fields = '__all__'
