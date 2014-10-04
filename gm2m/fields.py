from django.db.models.fields.related import RelatedField

from .relations import GM2MRel

from .compat import get_model_name, assert_compat_params


class GM2MField(RelatedField):
    """
    Provides a generic relation to several generic objects through a
    generic model storing content-type/object-id information

    Reverse relations can be established with models provided as arguments
    """

    def __init__(self, *related_models, **params):

        assert_compat_params(params)

        self.verbose_name = params.pop('verbose_name', None)

        self.rel = GM2MRel(self, related_models, **params)

        self.db_table = params.pop('db_table', None)
        if self.rel.through is not None:
            assert self.db_table is None, \
                'django-gm2m: Cannot specify a db_table if an intermediary ' \
                'model is used.'

    def add_relation(self, model):
        self.rel.add_relation(model)

    def get_reverse_path_info(self):
        linkfield = \
            self.through._meta.get_field_by_name(
                self.through._meta._field_names['src'])[0]
        return linkfield.get_reverse_path_info()

    def db_type(self, connection):
        """
        By default related field will not have a column as it relates
        columns to another table
        """
        return None

    def contribute_to_class(self, cls, name):
        """
        Appends accessor to a class and create intermediary model

        :param cls: the class to contribute to
        :param name: the name of the accessor
        """

        # attname is required for Django >= 1.7
        self.attname = self.name = name

        self.model = cls
        self.opts = cls._meta

        # Set up related classes if relations are defined
        self.rel.contribute_to_class(cls)

    def is_hidden(self):
        "Should the related object be hidden?"
        return self.rel.related_name and self.rel.related_name[-1] == '+'

    def related_query_name(self):
        return self.rel.related_query_name or self.rel.related_name \
            or get_model_name(self.rel.through)
