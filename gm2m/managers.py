from collections import defaultdict

import django
from django.db import router
from django.db.models import Manager, Q
from django.utils import six

from .query import GM2MTgtQuerySet
from .models import CT_ATTNAME, PK_ATTNAME
from .helpers import get_content_type


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
                     source_field_name):
            super(GM2MManager, self).__init__()

            self.instance = instance
            self.query_field_name = query_field_name

            self.core_filters = {}
            if rel:
                # we have a relation, so the manager's model is the source
                # model
                self.model = rel.field.model
                source_related_fields = []
                self.core_filters['related_objects__%s' % CT_ATTNAME] = get_content_type(instance)
                self.core_filters['related_objects__%s' % PK_ATTNAME] = instance.pk
            else:
                # we have no relation provided, the manager's model is the
                # through model
                self.model = through
                source_field = through._meta.get_field(source_field_name)
                source_related_fields = source_field.related_fields
                for __, rh_field in source_related_fields:
                    key = '%s__%s' % (query_field_name, rh_field.name)
                    self.core_filters[key] = getattr(instance,
                                                     rh_field.attname)

            self.through = through
            self.source_field_name = source_field_name

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
        if django.VERSION < (1, 6):
            get_query_set = get_queryset

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
                                 .filter(**{self.source_field_name:
                                                self._fk_val})
            to_add = []
            for ct, pks in six.iteritems(ct_pks):
                ctvals = vals.filter(**{'%s__exact' % CT_ATTNAME: ct.pk,
                                        '%s__in' % PK_ATTNAME: pks})
                for pk in pks.difference(ctvals):
                    to_add.append(self.through(**{
                        '%s_id' % self.source_field_name: self._fk_val,
                        CT_ATTNAME: ct,
                        PK_ATTNAME: pk
                    }))
            # Add the new entries in the db table
            self.through._default_manager.using(db).bulk_create(to_add)
        add.alters_data = True

        def remove(self, *objs):
            """
            Removes objects from the GM2M field
            """
            # *objs - objects to remove

            if not objs:
                return

            # sorting by content type to rationalise the number of queries
            q = Q()
            for obj in objs:
                # Convert the obj to (content_type, primary_key)
                q = q | Q(**{
                    CT_ATTNAME: get_content_type(obj),
                    PK_ATTNAME: obj.pk
                })

            db = router.db_for_write(self.through, instance=self.instance)
            self.through._default_manager.using(db).filter(**{
                '%s_id' % self.source_field_name: self._fk_val
            }).filter(q).delete()
        remove.alters_data = True

        def clear(self):
            db = router.db_for_write(self.through, instance=self.instance)
            self.through._default_manager.using(db).filter(**{
                '%s_id' % self.source_field_name: self._fk_val
            }).delete()
        clear.alters_data = True

    return GM2MManager
