from rest_framework import serializers

from .models import GeneralMapping, LocationEntityMapping


class GeneralMappingSerializer(serializers.ModelSerializer):
    """
    General mappings group serializer
    """
    class Meta:
        model = GeneralMapping
        fields = '__all__'


class LocationEntityMappingSerializer(serializers.ModelSerializer):
    """
    Location Entity Mappings group serializer
    """
    class Meta:
        model = LocationEntityMapping
        fields = '__all__'
