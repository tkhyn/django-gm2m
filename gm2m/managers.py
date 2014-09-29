from collections import defaultdict

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

    class GM2MManager(compat.Manager, superclass):
        def __init__(self, model, instance, through, rel, query_field_name,
                     field_names, prefetch_cache_name, gm2m_field):
            super(GM2MManager, self).__init__()

            self.instance = instance
            self.query_field_name = query_field_name
            self.prefetch_cache_name = prefetch_cache_name

            self.through = through
            self.rel = rel
            self.field_names = field_names
            self.field = gm2m_field

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
                self._mk_core_filters_norel(instance)

            self._fk_val = instance.pk

        def get_queryset(self):
            try:
                return self.instance \
                           ._prefetched_objects_cache[self.prefetch_cache_name]
            except (AttributeError, KeyError):
                db = self._db or router.db_for_read(self.instance.__class__,
                                                    instance=self.instance)
                return super(GM2MManager, self).get_queryset().using(db) \
                           ._next_is_sticky().filter(**self.core_filters)

        def get_prefetch_queryset(self, instances, queryset=None):
            if queryset is None:
                queryset = super(GM2MManager, self).get_queryset()

            db = self._db or router.db_for_read(self.model,
                                                instance=instances[0])

            join_table = self.through._meta.db_table
            connection = connections[db]
            qn = connection.ops.quote_name

            if self.rel:
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
                # instances (cf. implementation in compat)
                q = self._prefetch_qset_query_norel(instances)

                # Annotating the query in order to retrieve the primary model
                # id in the same query
                fk = self.through._meta.get_field(self.field_names['src'])
                extra_fields = compat.get_local_related_fields(fk)

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
                select_fields = compat.get_foreign_related_fields(fk)
                instance_attr = lambda inst: tuple([getattr(inst, f.attname)
                                    for f in select_fields])

            qs = queryset.using(db)._next_is_sticky().filter(q).extra(**extra)

            if not self.rel:
                # marking the queryset so that the original queryset should
                # be returned when evaluated the first time
                qs._related_prefetching = True

            return (qs,
                    rel_obj_attr,
                    instance_attr,
                    False,
                    self.prefetch_cache_name)

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

            if self.rel:
                # a relation is defined, that means that we're using the
                # reverse relation to add source model instances
                inst_ct = get_content_type(self.instance)
                inst_pk = self.instance._get_pk_val()

                vals = self.through._default_manager.using(db) \
                                   .values_list(self.field_names['src']) \
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

            else:

                # sorting by content type to rationalise the number of queries
                ct_objs = defaultdict(lambda: [])
                for obj in objs:
                    # Convert the obj to (content_type, primary_key)
                    obj_ct = get_content_type(obj)
                    ct_objs[obj_ct].append(obj)

                vals = self.through._default_manager.using(db) \
                                     .values_list(self.field_names['tgt_ct'],
                                                  self.field_names['tgt_fk']) \
                                     .filter(**{
                                         self.field_names['src']: self._fk_val
                                     })
                to_add = []
                for ct, instances in six.iteritems(ct_objs):
                    self.field.add_relation(compat.get_model(instances[0]))
                    pks = set(inst._get_pk_val() for inst in instances)
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

            if self.rel:
                # a relation is defined, that means that we're using the
                # reverse relation to delete source model instances
                inst_ct = get_content_type(self.instance)
                inst_pk = self.instance._get_pk_val()
                q = Q(**{
                    '%s_id__in' % self.field_names['src']:
                        [obj._get_pk_val() for obj in objs],
                    self.field_names['tgt_ct']: inst_ct,
                    self.field_names['tgt_fk']: inst_pk
                })
            else:
                q = Q()
                for obj in objs:
                    # Convert the obj to (content_type, primary_key)
                    q = q | Q(**{
                        self.field_names['tgt_ct']: get_content_type(obj),
                        self.field_names['tgt_fk']: obj.pk
                    })
                q = q & Q(**{
                    '%s_id' % self.field_names['src']: self._fk_val
                })

            db = router.db_for_write(self.through, instance=self.instance)
            self.through._default_manager.using(db).filter(q).delete()
        remove.alters_data = True

        def clear(self):
            db = router.db_for_write(self.through, instance=self.instance)

            if self.rel:
                f = {
                    self.field_names['tgt_ct']: get_content_type(self.instance),
                    self.field_names['tgt_fk']: self.instance._get_pk_val()
                }
            else:
                f = {
                    '%s_id' % self.field_names['src']: self._fk_val
                }

            self.through._default_manager.using(db).filter(**f).delete()
        clear.alters_data = True

    return GM2MManager
