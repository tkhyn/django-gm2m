from collections import defaultdict

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db.models import signals
from django.db.backends import util
from django.db import connection, router
from django.conf import settings


CT_ATTNAME = 'content_type'
PK_ATTNAME = 'object_id'
FK_ATTNAME = 'gfk'
FK_QS_NAME = FK_ATTNAME + '_set'


from django.db.models import Manager
from django.db.models.query import QuerySet, EmptyQuerySet


class GM2MQuerySet(QuerySet):
    """
    A QuerySet with a fetch_generic_relations() method to bulk fetch
    all generic related items.  Similar to select_related(), but for
    generic foreign keys. This wraps QuerySet.prefetch_related.
    """

    def iterator(self):
        """
        Override to return the actual object, not the GM2MObject
        """
        for i in super(GM2MQuerySet, self).iterator():
            yield getattr(i, FK_ATTNAME)

    def none(self):
        clone = self._clone(klass=EmptyGM2MQuerySet)
        if hasattr(clone.query, 'set_empty'):
            clone.query.set_empty()
        return clone


class EmptyGM2MQuerySet(GM2MQuerySet, EmptyQuerySet):
    def fetch_generic_relations(self, *args):
        return self


def create_gm2m_intermediate_model(field, klass):
    """
    Creates a generic M2M model for the GM2M field 'field' on model 'klass'
    """

    from django.db import models

    managed = klass._meta.managed
    name = '%s_%s' % (klass._meta.object_name, field.name)
    from_ = klass._meta.model_name.lower()

    meta = type('Meta', (object,), {
        'db_table': field._get_m2m_db_table(klass._meta),
        'managed': managed,
        'auto_created': klass,
        'app_label': klass._meta.app_label,
        'db_tablespace': klass._meta.db_tablespace,
        'unique_together': (from_, CT_ATTNAME, PK_ATTNAME),
        'verbose_name': '%s-generic relationship' % from_,
        'verbose_name_plural': '%s-generic relationships' % from_,
    })

    return type(str(name), (models.Model,), {
        'Meta': meta,
        '__module__': klass.__module__,
        from_: models.ForeignKey(klass, related_name='%s+' % name,
                                 db_tablespace=field.db_tablespace,
                                 db_constraint=field.db_constraint),
        CT_ATTNAME: models.ForeignKey(ContentType),
        PK_ATTNAME: models.CharField(max_length=255),
        FK_ATTNAME: generic.GenericForeignKey()
    })


def create_gm2m_related_manager():
    """
    Dynamically create a manager class that only concerns an instance
    """
    class GM2MManager(Manager):
        def __init__(self, instance, through):
            super(GM2MManager, self).__init__()

            self.instance = instance
            self._fk_val = instance.pk

            self.through = through
            self.core_filters = {'id__exact': instance.pk}

        def get_queryset(self):
            try:
                return self.instance._prefetched_objects_cache[self.prefetch_cache_name]
            except (AttributeError, KeyError):
                return GM2MQuerySet(self.through)._next_is_sticky().filter(**self.core_filters)

        def add(self, *objs):
            source_field_name = self.instance.__class__._meta.model_name.lower()
            # source_field_name: the PK fieldname in join table for the source object
            # *objs - object instances to add

            if not objs:
                return

            # sorting by content type to rationalise the number of queries
            ct_pks = defaultdict(lambda: set())
            for obj in objs:
                # Convert the obj to (content_type, primary_key)
                obj_ct = ContentType.objects.db_manager(obj._state.db) \
                                            .get_for_model(obj)
                obj_pk = obj.pk
                ct_pks[obj_ct].add(obj_pk)

            db = router.db_for_write(self.through, instance=self.instance)
            vals = self.through._default_manager.using(db) \
                                 .values_list(CT_ATTNAME, PK_ATTNAME) \
                                 .filter(**{source_field_name: self._fk_val})
            for ct, pks in ct_pks.iteritems():
                ctvals = vals.filter(**{'%s__exact' % CT_ATTNAME: ct.pk,
                                        '%s__in' % PK_ATTNAME: pks})
                pks.difference_update(ctvals)

            # Add the new entries in the db table
            self.through._default_manager.using(db).bulk_create([
                self.through(**{
                    '%s_id' % source_field_name: self._fk_val,
                    CT_ATTNAME: ct,
                    PK_ATTNAME: pk
                })
                for pk in pks
                for ct, pks in ct_pks.iteritems()
            ])

        def none(self):
            return GM2MQuerySet(self.through).none()

    return GM2MManager


class GM2MField(object):
    """
    Provides a generic relation to several generic objects through a
    generic model storing content-type/object-id information
    """

    def __init__(self, **kwargs):
        self.db_table = kwargs.pop('db_table', None)
        self.db_tablespace = settings.DEFAULT_INDEX_TABLESPACE
        self.db_constraint = True

    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self

        return create_gm2m_related_manager()(instance, self.to)

    def __set__(self, instance, values):
        mngr = self.to.objects
        for value in values:
            if value is not None:
                new_item, __ = self.rel.through.objects.get_or_create(
                    content_type=self.get_content_type(obj=value),
                    object_id=value._get_pk_val()
                )
                mngr.add(new_item)
                instance.save()

    def contribute_to_class(self, cls, name):
        self.name = name
        self.model = cls
        self.cache_attr = "_%s_cache" % name

        self.to = create_gm2m_intermediate_model(self, cls)
        cls._meta.add_virtual_field(self)

        signals.pre_init.connect(self.instance_pre_init, sender=cls,
                                 weak=False)

        # Connect myself as the descriptor for this field
        setattr(cls, name, self)

    def instance_pre_init(self, signal, sender, args, kwargs, **_kwargs):
        """
        Handles initializing objects with the generic FKs instead of
        content-type/object-id fields.
        """
        if self.name in kwargs:
            values = kwargs.pop(self.name)
            ct_values = []
            for v in values:
                ct_values.append({CT_ATTNAME: self.get_content_type(obj=v),
                                  PK_ATTNAME: v._get_pk_val()})
            kwargs[self.name] = ct_values

    def _get_m2m_db_table(self, opts):
        """
        M2M table name for this relation
        """
        return self.db_table \
            or util.truncate_name('%s_%s' % (opts.db_table, self.name),
                                  connection.ops.max_name_length())

    def get_prefetch_queryset(self, instances):
        # For efficiency, group the instances by content type and then do one
        # query per model
        fk_dict = defaultdict(set)
        # We need one intermediate instance for each group in order to get the
        # right db:
        inter_instance_dict = {}

        m2m_attname = self.model._meta.get_field(self.name).get_attname()
        q = None
        for instance in instances:
            q_ = getattr(instance, m2m_attname)
            if q:
                q = q | q_
            else:
                q = q_

        # one query here to get content types and object ids for all the
        # related objects
        for inter_instance in q:
            ct_id = getattr(inter_instance, CT_ATTNAME)
            if ct_id is not None:
                fk_val = getattr(inter_instance, self.fk_field)
                if fk_val is not None:
                    fk_dict[ct_id].add(fk_val)
                    inter_instance_dict[ct_id] = inter_instance

        ret_val = []
        for ct_id, fkeys in fk_dict.items():
            inter_instance = inter_instance_dict[ct_id]
            ct = self.get_content_type(id=ct_id,
                                       using=inter_instance._state.db)
            ret_val.extend(ct.get_all_objects_for_this_type(pk__in=fkeys))

        # For doing the join in Python, we have to match both the FK val and
        # the content type, so we use a callable that returns a (fk, class)
        # pair.
        def gfk_key(obj):
            ct_id = getattr(obj, CT_ATTNAME)
            if ct_id is None:
                return None
            else:
                model = self.get_content_type(id=ct_id, using=obj._state.db) \
                            .model_class()
                fk_f = getattr(obj, self.fk_field)
                return (model._meta.pk.get_prep_value(fk_f), model)

        return (ret_val,
                lambda obj: (obj._get_pk_val(), obj.__class__),
                gfk_key,
                True,
                self.cache_attr)
