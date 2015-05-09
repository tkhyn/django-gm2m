from django.db import router
from django.db.models import Q
from django.db import connections
from django.contrib.contenttypes.models import ContentType

from .query import GM2MTgtQuerySet
from .helpers import get_content_type

from . import compat


class GM2MBaseManager(compat.Manager):
    def __init__(self, instance):
        super(GM2MBaseManager, self).__init__()
        self.model = self._model  # see create_gm2m_related_manager
        self.instance = instance
        self.pk = instance.pk
        self.core_filters = {}

    def get_queryset(self):
        try:
            return self.instance \
                       ._prefetched_objects_cache[self.prefetch_cache_name]
        except (AttributeError, KeyError):
            db = self._db or router.db_for_read(self.instance.__class__,
                                                instance=self.instance)
            return self._get_queryset(using=db)._next_is_sticky() \
                       .filter(**self.core_filters)

    def _get_queryset(self, using):
        return super(GM2MBaseManager, self).get_queryset().using(using)

    def get_prefetch_queryset(self, instances, queryset=None):
        db = self._db or router.db_for_read(self.model,
                                            instance=instances[0])

        if queryset is None:
            queryset = self._get_queryset(db)

        qs, rel_obj_attr, instance_attr = \
            self._get_prefetch_queryset_params(instances, queryset, db)

        return (qs,
                rel_obj_attr,
                instance_attr,
                False,
                self.prefetch_cache_name)

    def _get_extra_queryset(self, queryset, q, extra_fields, db):
        join_table = self.through._meta.db_table
        connection = connections[db]
        qn = connection.ops.quote_name
        extra = dict(select=dict(
            ('_prefetch_related_val_%s' % f.attname,
            '%s.%s' % (qn(join_table), qn(f.column)))
            for f in extra_fields))
        return queryset.using(db)._next_is_sticky().filter(q).extra(**extra)

    def check_through_model(self, method_name):
        # If the GM2M relation has an intermediary model,
        # the add and remove methods are not available.
        if not self.through._meta.auto_created:
            opts = self.through._meta
            raise AttributeError(
                'Cannot use %s() on a ManyToManyField which specifies an '
                'intermediary model. Use %s.%s\'s Manager instead.'
                % (method_name, opts.app_label, opts.object_name))

    def add(self, *objs):
        """
        Adds objects to the GM2M field
        """
        # *objs - object instances to add

        self.check_through_model('add')

        if not objs:
            return

        db = router.db_for_write(self.through, instance=self.instance)

        # Add the new entries in the db table
        self.through._default_manager.using(db).bulk_create(
            self.to_add(objs, db))
    add.alters_data = True

    def remove(self, *objs):
        """
        Removes objects from the GM2M field
        """
        # *objs - objects to remove

        self.check_through_model('remove')

        if not objs:
            return

        db = router.db_for_write(self.through, instance=self.instance)
        self.through._default_manager.using(db).filter(
            self.to_remove(objs)).delete()
    remove.alters_data = True

    def clear(self):
        db = router.db_for_write(self.through, instance=self.instance)
        self.through._default_manager.using(db).filter(
            **self.to_clear()).delete()

    clear.alters_data = True


class GM2MBaseSrcManager(compat.Manager):
    def __init__(self, instance):
        # the manager's model is the source model
        super(GM2MBaseSrcManager, self).__init__(instance)
        self.core_filters['%s__%s' % (self.query_field_name,
                                      self.field_names['tgt_ct'])] = \
            get_content_type(self.instance)
        self.core_filters['%s__%s' % (self.query_field_name,
                                      self.field_names['tgt_fk'])] = \
            self.instance.pk

    def _get_prefetch_queryset_params(self, instances, queryset, db):

        # we're looking for generic target instances, which should be
        # converted to (content_type, primary_key) tuples

        q = Q()
        for obj in instances:
            q = q | Q(**{
                '%s__%s' % (self.query_field_name,
                            self.field_names['tgt_ct']):
                     get_content_type(obj),
                '%s__%s' % (self.query_field_name,
                            self.field_names['tgt_fk']):
                     obj.pk
            })

        # Annotating the query in order to retrieve the primary model
        # content type and id in the same query
        # content type must be the 1st element, see rel_obj_attr below
        extra_fields = (
            self.through._meta.get_field(self.field_names['tgt_ct']),
            self.through._meta.get_field(self.field_names['tgt_fk'])
        )

        qs = self._get_extra_queryset(queryset, q, extra_fields, db)

        # primary model retrieval function
        def rel_obj_attr(relobj):
            t = []
            for f in extra_fields:
                try:
                    # t already contains the content type id
                    # we use get_for_id to retrieve the cached content type
                    model = ContentType.objects.get_for_id(t[0]).model_class()
                except IndexError:
                    # t is empty
                    model = ContentType
                t.append(model._meta.pk.to_python(
                    getattr(relobj, '_prefetch_related_val_%s' % f.attname)
                ))
            return tuple(t)

        # model attribute retrieval function
        instance_attr = lambda inst: \
            (get_content_type(inst).pk, inst.pk)

        return qs, rel_obj_attr, instance_attr

    def to_add(self, objs, db):
        # we're using the reverse relation to add source model
        # instances
        inst_ct = get_content_type(self.instance)
        vals = self.through._default_manager.using(db) \
                           .values_list(self.field_names['src'],
                                        flat=True) \
                           .filter(**{
                               self.field_names['tgt_ct']: inst_ct,
                               self.field_names['tgt_fk']: self.pk
                           })
        to_add = []
        for obj in objs:
            if obj.pk not in vals:
                to_add.append(self.through(**{
                    '%s_id' % self.field_names['src']:
                        obj.pk,
                    self.field_names['tgt_ct']: inst_ct,
                    self.field_names['tgt_fk']: self.pk
                }))
        return to_add

    def to_remove(self, objs):
        # we're using the reverse relation to delete source model
        # instances
        inst_ct = get_content_type(self.instance)
        return Q(**{
            '%s_id__in' % self.field_names['src']:
                [obj.pk for obj in objs],
            self.field_names['tgt_ct']: inst_ct,
            self.field_names['tgt_fk']: self.pk
        })

    def to_clear(self):
        return {
            self.field_names['tgt_ct']: get_content_type(self.instance),
            self.field_names['tgt_fk']: self.instance.pk
        }


class GM2MBaseTgtManager(compat.Manager):

    def __init__(self, instance):
        # the manager's model is the through model
        super(GM2MBaseTgtManager, self).__init__(instance)
        self._mk_core_filters_norel(self.instance)

    def _get_queryset(self, using):
        return GM2MTgtQuerySet(self.model, using=using)

    def _get_prefetch_queryset_params(self, instances, queryset, db):

        # we're looking for through model instances (cf. implementation
        # in compat)
        q = self._prefetch_qset_query_norel(instances)

        # Annotating the query in order to retrieve the primary model
        # id in the same query
        fk = self.through._meta.get_field(self.field_names['src'])
        extra_fields = compat.get_local_related_fields(fk)

        qs = self._get_extra_queryset(queryset, q, extra_fields, db)
        # marking the queryset so that the original queryset should
        # be returned when evaluated the first time
        qs._related_prefetching = True

        # primary model retrieval function
        def rel_obj_attr(relobj):
            t = []
            for f in extra_fields:
                v = getattr(relobj,
                            '_prefetch_related_val_%s' % f.attname)
                try:
                    v = v.pop()
                except AttributeError:  # v is not a list
                    pass
                t.append(compat.get_related_model(f)._meta.pk.to_python(v))
            return tuple(t)

        # model attribute retrieval function
        select_fields = compat.get_foreign_related_fields(fk)
        instance_attr = lambda inst: tuple([getattr(inst, f.attname)
                            for f in select_fields])

        return qs, rel_obj_attr, instance_attr

    def to_add(self, objs, db):
        models = []
        objs_set = set()
        for obj in objs:
            # extract content type and primary key for each object
            objs_set.add((get_content_type(obj),
                          obj.pk))
            m = obj.__class__
            if m not in models:
                # call field.add_relation for each model
                models.append(m)
                self.field.add_relation(m)

        vals = self.through._default_manager.using(db) \
                   .filter(**{self.field_names['src']: self.pk}) \
                   .values_list(self.field_names['tgt_ct'],
                                self.field_names['tgt_fk'])

        to_add = []
        for ct, pk in objs_set.difference(vals):
            to_add.append(self.through(**{
                '%s_id' % self.field_names['src']: self.pk,
                self.field_names['tgt_ct']: ct,
                self.field_names['tgt_fk']: pk
            }))

        return to_add

    def to_remove(self, objs):
        q = Q()
        for obj in objs:
            # Convert the obj to (content_type, primary_key)
            q = q | Q(**{
                self.field_names['tgt_ct']: get_content_type(obj),
                self.field_names['tgt_fk']: obj.pk
            })
        return q & Q(**{
            '%s_id' % self.field_names['src']: self.pk
        })

    def to_clear(self):
        return {
            '%s_id' % self.field_names['src']: self.pk
        }


def create_gm2m_related_manager(superclass=None, **kwargs):
    """
    Dynamically create a manager class that only concerns an instance (source
    or target)
    """

    bases = [GM2MBaseManager]

    if superclass is None:
        # no superclass provided, the manager is a generic target model manager
        bases.insert(0, GM2MBaseTgtManager)
    else:
        # superclass provided, the manager is a source model manager and also
        # derives from superclass
        bases.insert(0, GM2MBaseSrcManager)
        bases.append(superclass)

    # Django's Manager constructor sets model to None, we store it under the
    # class's attribute '_model' and it is retrieved in __init__
    kwargs['_model'] = kwargs.pop('model')
    return type(compat.Manager)('GM2MManager', tuple(bases), kwargs)
