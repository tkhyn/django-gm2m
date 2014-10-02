from django.db.models import Q
from django.db.models.deletion import CASCADE, DO_NOTHING
from django.db.utils import DEFAULT_DB_ALIAS

from .compat import RelatedObject
from .helpers import get_content_type
from .signals import deleting_src, deleting_tgt


def CASCADE_SIGNAL(collector, field, sub_objs, using):
    deleting_src.send(field.rel.to, objs=sub_objs)
    CASCADE(collector, field, sub_objs, using)


def CASCADE_SIGNAL_VETO(collector, field, sub_objs, using):
    results = deleting_src.send(field.rel.to, objs=sub_objs)
    if not any(r[1] for r in results):
        # if no receiver returned a truthy result (veto), we can
        # cascade-collect, else we do nothing
        CASCADE(collector, field, sub_objs, using)


def DO_NOTHING_SIGNAL(collector, field, sub_objs, using):
    deleting_src.send(field.rel.to, objs=sub_objs)


class GM2MRelatedObject(RelatedObject):

    unique = False
    generate_reverse_relation = False  # not used on Django < 1.7

    def __init__(self, parent_model, model, field, rel):
        super(GM2MRelatedObject, self).__init__(parent_model, model, field)
        self.rel = self.rels = rel

    def bulk_related_objects(self, objs, using=DEFAULT_DB_ALIAS):
        """
        Return all objects related to objs
        The returned result will be passed to Collector.collect, so one should
        not use the deletion functions as such
        """

        through = self.field.rels.through
        base_mngr = through._base_manager.db_manager(using)

        on_delete = self.rel.on_delete

        if on_delete is not DO_NOTHING:
            # collect related objects
            field_names = through._meta._field_names
            q = Q()
            for obj in objs:
                # Convert each obj to (content_type, primary_key)
                q = q | Q(**{
                    field_names['tgt_ct']: get_content_type(obj),
                    field_names['tgt_fk']: obj.pk
                })
            qs = base_mngr.filter(q)

            if on_delete in (DO_NOTHING_SIGNAL, CASCADE_SIGNAL,
                             CASCADE_SIGNAL_VETO):
                results = deleting_tgt.send(self.rel.to, objs=qs)

            if on_delete in (CASCADE, CASCADE_SIGNAL) \
            or on_delete is CASCADE_SIGNAL_VETO \
            and not any(r[1] for r in results):
                # if CASCADE must be called or if no receiver returned a veto
                # we return the qs for deletion
                return qs

        # do not delete anything by default
        empty_qs = base_mngr.none()
        empty_qs.query.set_empty()
        return empty_qs
