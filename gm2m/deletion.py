from django.db.models import Q
from django.db.models.deletion import CASCADE
from django.db.utils import DEFAULT_DB_ALIAS

from .compat import RelatedObject
from .helpers import get_content_type


class GM2MRelatedObject(RelatedObject):

    unique = False
    generate_reverse_relation = False  # not used on Django < 1.7

    def __init__(self, parent_model, model, field, rel):
        super(GM2MRelatedObject, self).__init__(parent_model, model, field)
        self.rel = self.rels = rel

    def bulk_related_objects(self, objs, using=DEFAULT_DB_ALIAS):
        """
        Return all objects related to objs
        """

        through = self.field.rels.through
        base_mngr = through._base_manager.db_manager(using)

        if self.rel.on_delete == CASCADE:
            field_names = through._meta._field_names
            q = Q()
            for obj in objs:
                # Convert each obj to (content_type, primary_key)
                q = q | Q(**{
                    field_names['tgt_ct']: get_content_type(obj),
                    field_names['tgt_fk']: obj.pk
                })
            return base_mngr.filter(q)

        # do nothing by default
        empty_qs = base_mngr.none()
        empty_qs.query.set_empty()
        return empty_qs
