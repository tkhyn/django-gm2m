from collections import defaultdict

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db.backends import util
from django.db import connection, router
from django.db.models import Manager
from django.db.models.fields.related import ReverseManyRelatedObjectsDescriptor
from django.db.models.query import QuerySet
from django.utils.functional import cached_property

CT_ATTNAME = 'content_type'
PK_ATTNAME = 'object_id'
FK_ATTNAME = 'gfk'
FK_QS_NAME = FK_ATTNAME + '_set'


def get_content_type(obj):
    return ContentType.objects.db_manager(obj._state.db).get_for_model(obj)


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


def create_gm2m_intermediate_model(field, klass):
    """
    Creates a generic M2M model for the GM2M field 'field' on model 'klass'
    """

    from django.db import models

    managed = klass._meta.managed
    name = '%s_%s' % (klass._meta.object_name, field.name)
    from_ = klass._meta.model_name

    db_table = util.truncate_name('%s_%s' % (klass._meta.db_table, field.name),
                                  connection.ops.max_name_length())

    meta = type('Meta', (object,), {
        'db_table': db_table,
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
        from_: models.ForeignKey(klass),
        CT_ATTNAME: models.ForeignKey(ContentType),
        PK_ATTNAME: models.CharField(max_length=16),
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
            self.src_field_name = self.instance.__class__._meta.model_name

            self.through = through
            self.core_filters = {'%s_id' % self.src_field_name: instance.pk}

        def get_queryset(self):
            try:
                return self.instance \
                           ._prefetched_objects_cache[self.prefetch_cache_name]
            except (AttributeError, KeyError):
                return GM2MQuerySet(self.through)._next_is_sticky() \
                                                 .filter(**self.core_filters)

        def add(self, *objs):
            """
            Adds objects to the GM2M field
            """
            # *objs - object instances to add

            if not objs:
                return

            # sorting by content type to rationalise the number of queries
            ct_pks = defaultdict(lambda: set())
            for obj in objs:
                # Convert the obj to (content_type, primary_key)
                obj_ct = get_content_type(obj)
                obj_pk = obj.pk
                ct_pks[obj_ct].add(obj_pk)

            db = router.db_for_write(self.through, instance=self.instance)
            vals = self.through._default_manager.using(db) \
                                 .values_list(CT_ATTNAME, PK_ATTNAME) \
                                 .filter(**{self.src_field_name: self._fk_val})
            for ct, pks in ct_pks.iteritems():
                ctvals = vals.filter(**{'%s__exact' % CT_ATTNAME: ct.pk,
                                        '%s__in' % PK_ATTNAME: pks})
                pks.difference_update(ctvals)

            # Add the new entries in the db table
            to_add = []
            for ct, pks in ct_pks.iteritems():
                for pk in pks:
                    to_add.append(self.through(**{
                        '%s_id' % self.src_field_name: self._fk_val,
                        CT_ATTNAME: ct,
                        PK_ATTNAME: pk
                    }))
            self.through._default_manager.using(db).bulk_create(to_add)
        add.alters_data = True

        def clear(self):
            db = router.db_for_write(self.through, instance=self.instance)
            self.through._default_manager.using(db).filter(**{
                '%s_id' % self.src_field_name: self._fk_val
            }).delete()
        clear.alters_data = True

    return GM2MManager


class GM2MDescriptor(ReverseManyRelatedObjectsDescriptor):
    """
    Provides a generic many-to-many descriptor to make the related manager
    available from the source model class
    """

    @property
    def through(self):
        return self.field.through

    @cached_property
    def related_manager_cls(self):
        return create_gm2m_related_manager()

    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self
        return self.related_manager_cls(instance, self.field.through)

    def __set__(self, instance, value):
        manager = self.__get__(instance)
        manager.clear()
        manager.add(*value)


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
