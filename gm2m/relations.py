from django.db.models.fields.related import add_lazy_relation
from django.contrib.contenttypes.generic import GenericForeignKey
from django.utils import six

from .models import create_gm2m_intermediary_model
from .descriptors import GM2MRelatedDescriptor
from .compat import ForeignObjectRel, is_swapped, add_related_field, \
                    get_model_name
from .deletion import CASCADE, GM2MRelatedObject

# default relation attributes
REL_ATTRS = {
    'related_name': None,
    'related_query_name': None,
    'through': None,
    'db_constraint': True,
    'for_concrete_model': True,
    'on_delete': CASCADE,
}


class GM2MRelBase(ForeignObjectRel):
    # this is a separate implementation from GM2M below for compatibility
    # reasons (see compat.add_related_field)

    def __init__(self, field, to):
        super(GM2MRelBase, self).__init__(field, to)
        self.multiple = True

    def get_related_field(self):
        """
        Returns the field in the to object to which this relationship is tied
        (this is always the primary key on the target model).
        """
        return self.to._meta.pk


class GM2MRel(GM2MRelBase):

    def __getattribute__(self, name):
        """
        General attributes are those from the GM2MRels object
        """
        sup = super(GM2MRel, self).__getattribute__
        if name in REL_ATTRS.keys():
            if name == 'on_delete':
                name += '_tgt'
            return getattr(sup('field').rels, name)
        else:
            return sup(name)

    def contribute_to_class(self):
        if isinstance(self.to, six.string_types) or self.to._meta.pk is None:
            def resolve_related_class(rel, model, cls):
                rel.to = model
                rel.do_related_class()
            add_lazy_relation(self.fields.model, self, self.to,
                              resolve_related_class)
        else:
            self.do_related_class()

    def do_related_class(self):
        # check that the relation does not already exist
        all_rels = self.field.rels.rels
        if self.to in [r.to for r in all_rels if r != self]:
            # if it does, it needs to be removed from the list, and no further
            # action should be taken
            all_rels.remove(self)
            return

        self.related = GM2MRelatedObject(self.to, self.field.model,
                                         self.field, self)
        if not self.field.model._meta.abstract:
            self.contribute_to_related_class()

    def contribute_to_related_class(self):
        """
        Appends accessors to related classes
        """

        # Internal M2Ms (i.e., those with a related name ending with '+')
        # and swapped models don't get a related descriptor.
        if not self.is_hidden() and not is_swapped(self.related.model):
            add_related_field(self.to._meta, self.related)
            setattr(self.to, self.related_name
                        or (get_model_name(self.field.model._meta) + '_set'),
                    GM2MRelatedDescriptor(self.related, self))


class GM2MRels(object):

    def __init__(self, field, related_models, **params):

        self.field = field

        for name, default in six.iteritems(REL_ATTRS):
            setattr(self, name, params.pop(name, default))

        self.on_delete_src = params.pop('on_delete_src', self.on_delete)
        self.on_delete_tgt = params.pop('on_delete_tgt', self.on_delete)

        if self.through and not self.db_constraint:
            raise ValueError('django-gm2m: Can\'t supply a through model '
                             'with db_constraint=False')

        self.rels = []
        for model in related_models:
            self.add_relation(model, contribute_to_class=False)

    def add_relation(self, model, contribute_to_class=True):
        try:
            assert not model._meta.abstract, \
            "%s cannot define a relation with abstract class %s" \
            % (self.field.__class__.__name__, model._meta.object_name)
        except AttributeError:
            # to._meta doesn't exist, so it must be a string
            assert isinstance(model, six.string_types), \
            '%s(%r) is invalid. First parameter to GM2MField must ' \
            'be either a model or a model name' \
            % (self.field.__class__.__name__, model)

        rel = GM2MRel(self.field, model)
        self.rels.append(rel)
        if contribute_to_class:
            rel.contribute_to_class()

    def contribute_to_class(self, cls):

        if not self.through:
            self.through = create_gm2m_intermediary_model(self.field, cls)
        cls._meta.add_virtual_field(self.field)

        # set related name
        if not self.field.model._meta.abstract and self.related_name:
            self.related_name = self.related_name % {
                'class': self.field.model.__name__.lower(),
                'app_label': self.field.model._meta.app_label.lower()
            }

        def calc_field_names(rels):
            # Extract field names from through model
            field_names = {}
            for f in rels.through._meta.fields:
                if hasattr(f, 'rel') and f.rel \
                and (f.rel.to == rels.field.model
                     or f.rel.to == '%s.%s' % (rels.field.model.__module__,
                                               rels.field.model.__name__)):
                    field_names['src'] = f.name
                    break
            for f in rels.through._meta.virtual_fields:
                if isinstance(f, GenericForeignKey):
                    field_names['tgt'] = f.name
                    field_names['tgt_ct'] = f.ct_field
                    field_names['tgt_fk'] = f.fk_field
                    break

            if not set(field_names.keys()).issuperset(('src', 'tgt')):
                raise ValueError('Bad through model for GM2M relationship.')

            rels.through._meta._field_names = field_names

        # resolve through model if it's provided as a string
        if isinstance(self.through, six.string_types):
            def resolve_through_model(rels, model, cls):
                self.through = model
                calc_field_names(rels)
            add_lazy_relation(cls, self, self.through, resolve_through_model)
        else:
            calc_field_names(self)

        for rel in self.rels:
            rel.contribute_to_class()
