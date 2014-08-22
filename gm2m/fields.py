from django.db.models.fields.related import RelatedField, RelatedObject, \
    add_lazy_relation, RECURSIVE_RELATIONSHIP_CONSTANT
from django.db.models.related import PathInfo
from django.utils import six

from .models import create_gm2m_intermediary_model, SRC_ATTNAME, TGT_ATTNAME
from .descriptors import GM2MRelatedDescriptor, ReverseGM2MRelatedDescriptor
from .relations import GM2MRel


class GM2MRelatedObject(RelatedObject):

    def __init__(self, parent_model, model, field, rel):
        super(GM2MRelatedObject, self).__init__(parent_model, model, field)
        self.rel = rel

    def get_accessor_name(self):
        if self.rel.multiple:
            # If this is a symmetrical m2m relation on self, there is no
            # reverse accessor.
            if getattr(self.rel, 'symmetrical', False) \
            and self.model == self.parent_model:
                return None
            return self.rel.related_name or (self.opts.model_name + '_set')
        else:
            return self.rel.related_name or (self.opts.model_name)


class GM2MField(RelatedField):
    """
    Provides a generic relation to several generic objects through a
    generic model storing content-type/object-id information

    Reverse relations can be established with models provided as arguments
    """

    def __init__(self, *related_models):
        self.rels = []
        for r in related_models:
            to = r
            try:
                assert not to._meta.abstract, \
                "%s cannot define a relation with abstract class %s" \
                % (self.__class__.__name__, to._meta.object_name)
            except AttributeError:
                # to._meta doesn't exist, so it must be a string
                assert isinstance(to, six.string_types), \
                '%s(%r) is invalid. First parameter to ManyToManyField must ' \
                'be either a model, a model name, or the string %r' \
                % (self.__class__.__name__, to,
                   RECURSIVE_RELATIONSHIP_CONSTANT)

            self.rels.append(GM2MRel(self, to))

    def get_reverse_path_info(self):
        linkfield = self.through._meta.get_field_by_name(SRC_ATTNAME)[0]
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

        self.name = name
        self.model = cls
        self.cache_attr = "_%s_cache" % name

        self.through = create_gm2m_intermediary_model(self, cls)
        cls._meta.add_virtual_field(self)

        # Connect the descriptor for this field
        setattr(cls, name, ReverseGM2MRelatedDescriptor(self))

        # Set up related classes if relations are defined
        for rel in self.rels:
            rel.through = self.through
            if not cls._meta.abstract and rel.related_name:
                related_name = rel.related_name % {
                    'class': cls.__name__.lower(),
                    'app_label': cls._meta.app_label.lower()
                }
                rel.related_name = related_name

            other = rel.to
            if isinstance(other, six.string_types) or other._meta.pk is None:
                def resolve_related_class(field, model, cls, rel):
                    rel.to = model
                    field.do_related_class(model, cls, rel)
                add_lazy_relation(cls, self, other, resolve_related_class)
            else:
                self.do_related_class(other, cls, rel)

    def do_related_class(self, other, cls, rel):
        self.related = GM2MRelatedObject(other, cls, self, rel)
        if not cls._meta.abstract:
            self.contribute_to_related_class(other, self.related, rel)

    def contribute_to_related_class(self, cls, related, rel):
        """
        Appends accessors to related classes

        :param cls: the class to contribute to
        :param related: the related field
        :param rel: the relation object concerning cls and self.model
        """

        assert rel.to == cls, 'Bad relation object'

        # Internal M2Ms (i.e., those with a related name ending with '+')
        # and swapped models don't get a related descriptor.
        if not rel.is_hidden() and not related.model._meta.swapped:
            setattr(cls, related.get_accessor_name(),
                    GM2MRelatedDescriptor(related, rel))
