from django.db.backends import util
from django.db import connection
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from .compat import get_model_name, get_fk_kwargs, get_gfk_kwargs

SRC_ATTNAME = 'gm2m_src'
TGT_ATTNAME = 'gm2m_tgt'
CT_ATTNAME = 'gm2m_content_type'
FK_ATTNAME = 'gm2m_object_id'


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
        'unique_together': (SRC_ATTNAME, CT_ATTNAME, FK_ATTNAME),
        'verbose_name': '%s-generic relationship' % model_name,
        'verbose_name_plural': '%s-generic relationships' % model_name,
    })

    fk_kwargs = get_fk_kwargs(field)

    return type(str(name), (models.Model,), {
        'Meta': meta,
        '__module__': klass.__module__,
        SRC_ATTNAME: models.ForeignKey(klass,
                                       on_delete=field.rels.on_delete_src,
                                       **fk_kwargs),
        CT_ATTNAME: models.ForeignKey(ContentType, **fk_kwargs),
        FK_ATTNAME: models.CharField(max_length=16),
        TGT_ATTNAME: generic.GenericForeignKey(
                         ct_field=CT_ATTNAME,
                         fk_field=FK_ATTNAME,
                         **get_gfk_kwargs(field)
                     )
    })
