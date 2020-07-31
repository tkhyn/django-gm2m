"""
Yes, monkey-patching Django is not the greatest thing to do, but in that
case there is no other solution to make it alter *both* fields needed by the
GFK (content type + primary key)
"""

import django
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.backends.sqlite3.schema import DatabaseSchemaEditor
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.operations.models import RenameModel


# ALL BACKENDS EXCEPT SQLITE

_alter_many_to_many_0 = BaseDatabaseSchemaEditor._alter_many_to_many


def _alter_many_to_many(self, model, old_field, new_field, strict):
    from .fields import GM2MField
    if isinstance(old_field, GM2MField) \
    or isinstance(new_field, GM2MField):
        # Rename the through table
        if old_field.remote_field.through._meta.db_table != \
           new_field.remote_field.through._meta.db_table:
            self.alter_db_table(old_field.remote_field.through,
                                old_field.remote_field.through._meta.db_table,
                                new_field.remote_field.through._meta.db_table)
        # Repoint the GFK to the other side
        # we need to alter both fields of the GFK
        old_names = old_field.remote_field.through._meta._field_names
        new_names = new_field.remote_field.through._meta._field_names
        getoldfield = old_field.remote_field.through._meta.get_field
        getnewfield = new_field.remote_field.through._meta.get_field
        self.alter_field(
            new_field.remote_field.through,
            getoldfield(old_names['tgt_fk']),
            getnewfield(new_names['tgt_fk']),
        )
        self.alter_field(
            new_field.remote_field.through,
            getoldfield(old_names['tgt_ct']),
            getnewfield(new_names['tgt_ct']),
        )
        # now we alter the fk
        self.alter_field(
            new_field.remote_field.through,
            getoldfield(old_names['src']),
            getnewfield(new_names['src']),
        )
    else:
        return _alter_many_to_many_0(self, model, old_field, new_field,
                                     strict)
BaseDatabaseSchemaEditor._alter_many_to_many = _alter_many_to_many


# SQLITE BACKEND, SPECIFIC IMPLEMENTATION

_alter_many_to_many_sqlite0 = DatabaseSchemaEditor._alter_many_to_many


def _alter_many_to_many(self, model, old_field, new_field, strict):
    from .fields import GM2MField
    if isinstance(old_field, GM2MField) \
    or isinstance(new_field, GM2MField):
        # Repoint the GFK to the other side
        # we need to alter both fields of the GFK
        old_names = old_field.remote_field.through._meta._field_names
        new_names = new_field.remote_field.through._meta._field_names
        getoldfield = old_field.remote_field.through._meta.get_field
        getnewfield = new_field.remote_field.through._meta.get_field
        
        if old_field.remote_field.through._meta.db_table == \
        new_field.remote_field.through._meta.db_table:
            # The field name didn't change, but some options did;
            # we have to propagate this altering.
            # We need the field that points to the target model,
            # so we can tell alter_field to change it -
            # this is m2m_reverse_field_name() (as opposed to
            # m2m_field_name, which points to our model)
            for f in ['tgt_fk', 'tgt_ct']:
                self._remake_table(
                    old_field.remote_field.through,
                    alter_field=(
                        getoldfield(old_names[f]),
                        getnewfield(new_names[f]),
                    )
                )
            return

        # Make a new through table
        self.create_model(new_field.remote_field.through)
        # Copy the data across
        self.execute("INSERT INTO %s (%s) SELECT %s FROM %s" % (
            self.quote_name(new_field.remote_field.through._meta.db_table),
            ', '.join([
                "id",
                getnewfield(old_names['src']).column,
                getnewfield(old_names['tgt_fk']).column,
                getnewfield(old_names['tgt_ct']).column,
            ]),
            ', '.join([
                "id",
                getoldfield(old_names['src']).column,
                getoldfield(old_names['tgt_fk']).column,
                getoldfield(old_names['tgt_ct']).column,
            ]),
            self.quote_name(old_field.remote_field.through._meta.db_table),
        ))
        # Delete the old through table
        self.delete_model(old_field.remote_field.through)
    else:
        return _alter_many_to_many_sqlite0(self, model, old_field,
                                           new_field, strict)


DatabaseSchemaEditor._alter_many_to_many = _alter_many_to_many


def only_relation_agnostic_fields(self, fields):
    """
    We only change the way the 'model' key is deleted from the dict
    (as GM2MField.deconstruct does not return a 'model' kwarg)
    """
    fields_def = []

    fields_items = None
    if django.VERSION >= (3, 1):
        fields_items = sorted(fields.items())
    else:
        fields_items = sorted(fields)

    for __, field in fields_items:
        deconstruction = self.deep_deconstruct(field)
        if field.remote_field and field.remote_field.model:
            deconstruction[2].pop('model', None)
        fields_def.append(deconstruction)
    return fields_def

MigrationAutodetector.only_relation_agnostic_fields = \
    only_relation_agnostic_fields


database_forwards0 = RenameModel.database_forwards

def database_forwards(self, app_label, schema_editor, from_state, to_state):
    """
    Filter out auto created related objects from Options.related_objects
    """

    old_model = from_state.apps.get_model(app_label, self.old_name)
    related_objects_bck = old_model._meta.related_objects
    old_model._meta.related_objects = [o for o in related_objects_bck
                                       if not o.auto_created]

    database_forwards0(self, app_label, schema_editor, from_state, to_state)

    old_model._meta.related_objects = related_objects_bck

RenameModel.database_forwards = database_forwards
