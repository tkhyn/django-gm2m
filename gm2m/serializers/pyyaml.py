from django.core.serializers import pyyaml
from . import python


class Serializer(python.Serializer, pyyaml.Serializer):
    """
    As python.Serializer does not override anything from pyyaml.Serializer,
    nothing wrong with using the MRO
    """
    pass

Deserializer = pyyaml.Deserializer
