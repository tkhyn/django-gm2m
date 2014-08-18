from .models import create_gm2m_intermediate_model
from .descriptors import GM2MDescriptor


class GM2MField(object):
    """
    Provides a generic relation to several generic objects through a
    generic model storing content-type/object-id information
    """

    def contribute_to_class(self, cls, name):
        self.name = name
        self.model = cls
        self.cache_attr = "_%s_cache" % name

        self.through = create_gm2m_intermediate_model(self, cls)
        cls._meta.add_virtual_field(self)

        # Connect the descriptor for this field
        setattr(cls, name, GM2MDescriptor(self))
