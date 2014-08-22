from django.db.backends import util
from django.db import connection
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from .helpers import get_model_name

SRC_ATTNAME = 'gm2m_src'
TGT_ATTNAME = 'gm2m_tgt'
CT_ATTNAME = 'gm2m_content_type'
PK_ATTNAME = 'gm2m_object_id'


def create_gm2m_intermediary_model(field, klass):
    """
    Creates a generic M2M model for the GM2M field 'field' on model 'klass'
    """

    from django.db import models

    managed = klass._meta.managed
    name = '%s_%s' % (klass._meta.object_name, field.name)

    model_name = get_model_name(klass)

    db_table = util.truncate_name('%s_%s' % (klass._meta.db_table, field.name),
                                  connection.ops.max_name_length())

    meta = type('Meta', (object,), {
        'db_table': db_table,
        'managed': managed,
        'auto_created': klass,
        'app_label': klass._meta.app_label,
        'db_tablespace': klass._meta.db_tablespace,
        'unique_together': (SRC_ATTNAME, CT_ATTNAME, PK_ATTNAME),
        'verbose_name': '%s-generic relationship' % model_name,
        'verbose_name_plural': '%s-generic relationships' % model_name,
    })

    return type(str(name), (models.Model,), {
        'Meta': meta,
        '__module__': klass.__module__,
        SRC_ATTNAME: models.ForeignKey(klass),
        CT_ATTNAME: models.ForeignKey(ContentType),
        PK_ATTNAME: models.CharField(max_length=16),
        TGT_ATTNAME: generic.GenericForeignKey()
    })
