from django.core.serializers import json
from . import python


class Serializer(python.Serializer, json.Serializer):
    """
    As python.Serializer does not override anything from json.Serializer,
    nothing wrong with using the MRO
    """
    pass

Deserializer = json.Deserializer
