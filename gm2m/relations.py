from django.db.models.fields.related import add_lazy_relation
from django.contrib.contenttypes.generic import GenericForeignKey
from django.db.models.signals import pre_delete
from django.utils.functional import cached_property
from django.utils import six

from .models import create_gm2m_intermediary_model
from .managers import create_gm2m_related_manager
from .descriptors import GM2MRelatedDescriptor, ReverseGM2MRelatedDescriptor
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

    dummy_pre_delete = lambda s, **kwargs: None

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

        # this enables cascade deletion for any relation (even hidden ones)
        add_related_field(self.to._meta, self.related)

        # we connect a dummy receiver to pre_delete so that the model is not
        # 'fast_delete'-able
        # (see django.db.models.deletion.Collector.can_fast_delete)
        pre_delete.connect(self.dummy_pre_delete, sender=self.to)

        # Internal M2Ms (i.e., those with a related name ending with '+')
        # and swapped models don't get a related descriptor.
        if not self.is_hidden() and not is_swapped(self.related.model):
            setattr(self.to, self.related_name
                        or (get_model_name(self.field.model._meta) + '_set'),
                    GM2MRelatedDescriptor(self.related, self))

    @cached_property
    def related_manager_cls(self):
        # the related manager class getter is implemented here rather than in
        # the descriptor as we may need to access it even for hidden relations
        return create_gm2m_related_manager(
            superclass=self.to._default_manager.__class__,
            field=self.related.field,
            model=self.related.model,
            through=self.through,
            query_field_name=get_model_name(self.through),
            field_names=self.through._meta._field_names,
            prefetch_cache_name=self.related.field.related_query_name()
        )


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

        # Connect the descriptor for this field
        setattr(cls, self.field.attname,
                ReverseGM2MRelatedDescriptor(self.field))

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

    @cached_property
    def related_manager_cls(self):
        field_names = self.through._meta._field_names
        return create_gm2m_related_manager(
            superclass=None,
            field=self.field,
            model=self.through,
            through=self.through,
            query_field_name=field_names['src'],
            field_names=field_names,
            prefetch_cache_name=self.field.name
        )
