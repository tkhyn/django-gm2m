from django.db.models.query import QuerySet

from .models import FK_ATTNAME


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
