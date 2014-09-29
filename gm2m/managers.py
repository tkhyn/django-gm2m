from django.db import router
from django.db.models import Q, Manager
from django.db import connections
from django.utils import six

from .query import GM2MTgtQuerySet
from .helpers import get_content_type

from . import compat


class GM2MTgtManager(Manager):

    def get_queryset(self):
        return GM2MTgtQuerySet(self.model, using=self._db)


def create_gm2m_related_manager(superclass=GM2MTgtManager):
    """
    Dynamically create a manager class that only concerns an instance (source
    or target)
    """

    class GM2MManagerBase(compat.Manager, superclass):
        def __init__(self, field, model, instance, through, query_field_name,
                     field_names, prefetch_cache_name):
            super(GM2MManagerBase, self).__init__()

            self.field = field
            self.model = model
            self.instance = instance
            self._fk_val = instance._get_pk_val()
            self.through = through

            self.query_field_name = query_field_name
            self.field_names = field_names
            self.prefetch_cache_name = prefetch_cache_name

            self.core_filters = {}
            self.source_related_fields = None

        def get_queryset(self):
            try:
                return self.instance \
                           ._prefetched_objects_cache[self.prefetch_cache_name]
            except (AttributeError, KeyError):
                db = self._db or router.db_for_read(self.instance.__class__,
                                                    instance=self.instance)
                return super(GM2MManagerBase, self).get_queryset().using(db) \
                           ._next_is_sticky().filter(**self.core_filters)

        def get_prefetch_queryset(self, instances, queryset=None):
            if queryset is None:
                queryset = super(GM2MManagerBase, self).get_queryset()

            db = self._db or router.db_for_read(self.model,
                                                instance=instances[0])

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

    if superclass == GM2MTgtManager:
        # the manager is a generic target model manager
        class GM2MManager(GM2MManagerBase):
            def __init__(self, **kwargs):
                # the manager's model is the through model
                super(GM2MManager, self).__init__(**kwargs)
                self.model = self.through
                self._mk_core_filters_norel(self.instance)

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
                        t.append(relobj._meta.pk.to_python(v))
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
                                  obj._get_pk_val()))
                    m = compat.get_model(obj)
                    if m not in models:
                        # call field.add_relation for each model
                        models.append(m)
                        self.field.add_relation(m)

                vals = self.through._default_manager.using(db) \
                           .filter(**{self.field_names['src']: self._fk_val }) \
                           .values_list(self.field_names['tgt_ct'],
                                        self.field_names['tgt_fk'])

                to_add = []
                for ct, pk in objs_set.difference(vals):
                    to_add.append(self.through(**{
                        '%s_id' % self.field_names['src']: self._fk_val,
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
                    '%s_id' % self.field_names['src']: self._fk_val
                })

            def to_clear(self):
                return {
                    '%s_id' % self.field_names['src']: self._fk_val
                }

    else:
        class GM2MManager(GM2MManagerBase):
            def __init__(self, **kwargs):
                # the manager's model is the source model
                super(GM2MManager, self).__init__(**kwargs)
                self.core_filters['%s__%s' % (self.query_field_name,
                                              self.field_names['tgt_ct'])] = \
                    get_content_type(self.instance)
                self.core_filters['%s__%s' % (self.query_field_name,
                                              self.field_names['tgt_fk'])] = \
                    self.instance._get_pk_val()

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
                             obj._get_pk_val()
                    })

                # Annotating the query in order to retrieve the primary model
                # content type and id in the same query
                extra_fields = (
                    self.through._meta.get_field(self.field_names['tgt_ct']),
                    self.through._meta.get_field(self.field_names['tgt_fk'])
                )

                qs = self._get_extra_queryset(queryset, q, extra_fields, db)

                # primary model retrieval function
                def rel_obj_attr(relobj):
                    t = []
                    for f in extra_fields:
                        t.append(relobj._meta.pk.to_python(
                            getattr(relobj,
                                    '_prefetch_related_val_%s' % f.attname)))
                    return tuple(t)

                # model attribute retrieval function
                instance_attr = lambda inst: \
                    (get_content_type(inst)._get_pk_val(), inst._get_pk_val())

                return qs, rel_obj_attr, instance_attr

            def to_add(self, objs, db):
                # we're using the reverse relation to add source model
                # instances
                inst_ct = get_content_type(self.instance)
                inst_pk = self.instance._get_pk_val()

                vals = self.through._default_manager.using(db) \
                                   .values_list(self.field_names['src'],
                                                flat=True) \
                                   .filter(**{
                                       self.field_names['tgt_ct']: inst_ct,
                                       self.field_names['tgt_fk']: inst_pk
                                   })
                to_add = []
                for obj in objs:
                    if obj._get_pk_val() not in vals:
                        to_add.append(self.through(**{
                            '%s_id' % self.field_names['src']:
                                obj._get_pk_val(),
                            self.field_names['tgt_ct']: inst_ct,
                            self.field_names['tgt_fk']: inst_pk
                        }))
                return to_add

            def to_remove(self, objs):
                # we're using the reverse relation to delete source model
                # instances
                inst_ct = get_content_type(self.instance)
                inst_pk = self.instance._get_pk_val()
                return Q(**{
                    '%s_id__in' % self.field_names['src']:
                        [obj._get_pk_val() for obj in objs],
                    self.field_names['tgt_ct']: inst_ct,
                    self.field_names['tgt_fk']: inst_pk
                })

            def to_clear(self):
                return {
                    self.field_names['tgt_ct']: get_content_type(self.instance),
                    self.field_names['tgt_fk']: self.instance._get_pk_val()
                }

    return GM2MManager
