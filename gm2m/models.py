from django.db.backends import util
from django.db import connection
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic


CT_ATTNAME = 'content_type'
PK_ATTNAME = 'object_id'
FK_ATTNAME = 'gfk'


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
