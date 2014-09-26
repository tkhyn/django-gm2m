from collections import defaultdict

import django
from django.db import router
from django.db.models import Manager, Q
from django.db import connections
from django.utils import six

from .query import GM2MTgtQuerySet
from .helpers import get_content_type
from .compat import get_queryset


class GM2MTgtManager(Manager):

    def get_queryset(self):
        return GM2MTgtQuerySet(self.model, using=self._db)
    if django.VERSION < (1, 6):
        get_query_set = get_queryset


def create_gm2m_related_manager(superclass=GM2MTgtManager, rel=None):
    """
    Dynamically create a manager class that only concerns an instance (source
    or target)
    """
    class GM2MManager(superclass):
        def __init__(self, model, instance, through, query_field_name,
                     field_names, prefetch_cache_name):
            super(GM2MManager, self).__init__()

            self.instance = instance
            self.query_field_name = query_field_name
            self.prefetch_cache_name = prefetch_cache_name

            self.through = through
            self.field_names = field_names

            self.core_filters = {}
            self.source_related_fields = None
            if rel:
                # we have a relation, so the manager's model is the source
                # model
                self.model = rel.field.model
                self.core_filters['%s__%s' % (query_field_name,
                                              self.field_names['tgt_ct'])] = \
                    get_content_type(instance)
                self.core_filters['%s__%s' % (query_field_name,
                                              self.field_names['tgt_fk'])] = \
                    instance._get_pk_val()
            else:
                # we have no relation provided, the manager's model is the
                # through model
                self.model = through

                if django.VERSION < (1, 6):
                    self.core_filters = {'%s__pk' % query_field_name:
                                         instance._get_pk_val()}
                else:
                    source_field = through._meta.get_field(
                                       self.field_names['src'])
                    self.source_related_fields = source_field.related_fields
                    for __, rh_field in self.source_related_fields:
                        key = '%s__%s' % (query_field_name, rh_field.name)
                        self.core_filters[key] = getattr(instance,
                                                         rh_field.attname)

            self._fk_val = instance.pk

        def get_queryset(self):
            try:
                return self.instance \
                           ._prefetched_objects_cache[self.prefetch_cache_name]
            except (AttributeError, KeyError):
                db = self._db or router.db_for_read(self.instance.__class__,
                                                    instance=self.instance)
                return get_queryset(super(GM2MManager, self)).using(db) \
                           ._next_is_sticky().filter(**self.core_filters)

        def get_prefetch_queryset(self, instances, queryset=None):
            if queryset is None:
                queryset = get_queryset(super(GM2MManager, self))

            db = self._db or router.db_for_read(self.model,
                                                instance=instances[0])

            join_table = self.through._meta.db_table
            connection = connections[db]
            qn = connection.ops.quote_name

            if rel:
                # without a specified relation, we're looking for generic
                # target instances, which should be converted to
                # (content_type, primary_key)
                q = Q()
                for obj in instances:
                    q = q | Q(**{
                        '%s__%s' % (self.query_field_name,
                                    self.field_names['tgt_ct']):
                             get_content_type(obj),
                        '%s__%s' % (self.query_field_name,
                                    self.field_names['tgt_fk']):
                             obj._get_pk_val()
                    })

                # Annotating the query in order to retrieve the primary model
                # content type and id in the same query
                related_fields = (
                    self.through._meta.get_field(self.field_names['tgt_ct']),
                    self.through._meta.get_field(self.field_names['tgt_fk'])
                )
                extra = dict(select=dict(
                    ('_prefetch_related_val_%s' % f.attname,
                    '%s.%s' % (qn(join_table), qn(f.column)))
                    for f in related_fields))

                # primary model retrieval function
                def rel_obj_attr(relobj):
                    t = []
                    for f in related_fields:
                        t.append(relobj._meta.pk.to_python(
                            getattr(relobj,
                                    '_prefetch_related_val_%s' % f.attname)))
                    return tuple(t)

                # model attribute retrieval function
                instance_attr = lambda inst: \
                    (get_content_type(inst)._get_pk_val(), inst._get_pk_val())

            else:
                # without a specified relation, we're looking for through model
                # instances
                query = {}
                if django.VERSION < (1, 6):
                    query = {'%s_id__in' % self.field_names['src']:
                        set(obj._get_pk_val() for obj in instances)}
                else:
                    for lh_field, rh_field in self.source_related_fields:
                        query['%s__in' % lh_field.name] = \
                            set(getattr(obj, rh_field.attname)
                                for obj in instances)
                q = Q(**query)

                # Annotating the query in order to retrieve the primary model
                # id in the same query
                fk = self.through._meta.get_field(self.field_names['src'])
                try:
                    extra_fields = fk.local_related_fields
                except AttributeError:  # django < 1.6, no local_related_fields
                    extra_fields = (fk,)

                extra = dict(select=dict(
                    ('_prefetch_related_val_%s' % f.attname,
                    '%s.%s' % (qn(join_table), qn(f.column)))
                    for f in extra_fields))

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
                        t.append(relobj._meta.pk.to_python(v))
                    return tuple(t)

                # model attribute retrieval function
                try:
                    select_fields = fk.foreign_related_fields
                except AttributeError:  # django 1.6
                    select_fields = (fk.rel.get_related_field(),)
                instance_attr = lambda inst: tuple([getattr(inst, f.attname)
                                    for f in select_fields])

            qs = queryset.using(db)._next_is_sticky().filter(q).extra(**extra)

            if not rel:
                # marking the queryset so that the original queryset should
                # be returned when evaluated the first time
                qs._related_prefetching = True

            return (qs,
                    rel_obj_attr,
                    instance_attr,
                    False,
                    self.prefetch_cache_name)

        if django.VERSION < (1, 6):
            get_query_set = get_queryset
            get_prefetch_query_set = get_prefetch_queryset

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

            # sorting by content type to rationalise the number of queries
            ct_pks = defaultdict(lambda: set())
            for obj in objs:
                # Convert the obj to (content_type, primary_key)
                obj_ct = get_content_type(obj)
                obj_pk = obj.pk
                ct_pks[obj_ct].add(obj_pk)

            db = router.db_for_write(self.through, instance=self.instance)
            vals = self.through._default_manager.using(db) \
                                 .values_list(self.field_names['tgt_ct'],
                                              self.field_names['tgt_fk']) \
                                 .filter(**{self.field_names['src']:
                                                self._fk_val})
            to_add = []
            for ct, pks in six.iteritems(ct_pks):
                ctvals = vals.filter(**{'%s__exact' %
                                        self.field_names['tgt_ct']: ct.pk,
                                        '%s__in' %
                                        self.field_names['tgt_fk']: pks})
                for pk in pks.difference(ctvals):
                    to_add.append(self.through(**{
                        '%s_id' % self.field_names['src']: self._fk_val,
                        self.field_names['tgt_ct']: ct,
                        self.field_names['tgt_fk']: pk
                    }))
            # Add the new entries in the db table
            self.through._default_manager.using(db).bulk_create(to_add)
        add.alters_data = True

        def remove(self, *objs):
            """
            Removes objects from the GM2M field
            """
            # *objs - objects to remove

            self.check_through_model('remove')

            if not objs:
                return

            # sorting by content type to rationalise the number of queries
            q = Q()
            for obj in objs:
                # Convert the obj to (content_type, primary_key)
                q = q | Q(**{
                    self.field_names['tgt_ct']: get_content_type(obj),
                    self.field_names['tgt_fk']: obj.pk
                })

            db = router.db_for_write(self.through, instance=self.instance)
            self.through._default_manager.using(db).filter(**{
                '%s_id' % self.field_names['src']: self._fk_val
            }).filter(q).delete()
        remove.alters_data = True

        def clear(self):
            db = router.db_for_write(self.through, instance=self.instance)
            self.through._default_manager.using(db).filter(**{
                '%s_id' % self.field_names['src']: self._fk_val
            }).delete()
        clear.alters_data = True

    return GM2MManager
