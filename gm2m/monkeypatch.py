"""
Yes, monkey-patching Django is not the greatest thing to do, but in that
case there is no other solution to make it alter *both* fields needed by the
GFK (content type + primary key)
"""

try:
    # Will be ignored for Django < 1.7

    # ALL BACKENDS EXCEPT SQLITE

    try:
        # django 1.8
        from django.db.backends.base.schema import BaseDatabaseSchemaEditor
    except ImportError:
        # django 1.7
        from django.db.backends.schema import BaseDatabaseSchemaEditor

    _alter_many_to_many_0 = BaseDatabaseSchemaEditor._alter_many_to_many

    def _alter_many_to_many(self, model, old_field, new_field, strict):
        from .fields import GM2MField
        if isinstance(old_field, GM2MField) \
        or isinstance(new_field, GM2MField):
            # Rename the through table
            if old_field.rel.through._meta.db_table != \
               new_field.rel.through._meta.db_table:
                self.alter_db_table(old_field.rel.through,
                                    old_field.rel.through._meta.db_table,
                                    new_field.rel.through._meta.db_table)
            # Repoint the GFK to the other side
            # we need to alter both fields of the GFK
            old_names = old_field.rel.through._meta._field_names
            new_names = new_field.rel.through._meta._field_names
            gfbn_old = old_field.rel.through._meta.get_field_by_name
            gfbn_new = new_field.rel.through._meta.get_field_by_name
            self.alter_field(
                new_field.rel.through,
                gfbn_old(old_names['tgt_fk'])[0],
                gfbn_new(new_names['tgt_fk'])[0],
            )
            self.alter_field(
                new_field.rel.through,
                gfbn_old(old_names['tgt_ct'])[0],
                gfbn_new(new_names['tgt_ct'])[0],
            )
            # now we alter the fk
            self.alter_field(
                new_field.rel.through,
                gfbn_old(old_names['src'])[0],
                gfbn_new(new_names['src'])[0],
            )
        else:
            return _alter_many_to_many_0(self, model, old_field, new_field,
                                         strict)
    BaseDatabaseSchemaEditor._alter_many_to_many = _alter_many_to_many

    # SQLITE BACKEND, SPECIFIC IMPLEMENTATION

    from django.db.backends.sqlite3.schema import DatabaseSchemaEditor

    _alter_many_to_many_sqlite0 = DatabaseSchemaEditor._alter_many_to_many

    def _alter_many_to_many(self, model, old_field, new_field, strict):
        from .fields import GM2MField
        if isinstance(old_field, GM2MField) \
        or isinstance(new_field, GM2MField):
            # Repoint the GFK to the other side
            # we need to alter both fields of the GFK
            old_names = old_field.rel.through._meta._field_names
            new_names = new_field.rel.through._meta._field_names
            gfbn_old = old_field.rel.through._meta.get_field_by_name
            gfbn_new = new_field.rel.through._meta.get_field_by_name

            if old_field.rel.through._meta.db_table == \
            new_field.rel.through._meta.db_table:
                # The field name didn't change, but some options did;
                # we have to propagate this altering.
                self._remake_table(
                    old_field.rel.through,
                    # We need the field that points to the target model,
                    # so we can tell alter_field to change it -
                    # this is m2m_reverse_field_name() (as opposed to
                    # m2m_field_name, which points to our model)
                    alter_fields=[(
                        gfbn_old(old_names['tgt_fk'])[0],
                        gfbn_new(new_names['tgt_fk'])[0],
                    ),
                    (
                        gfbn_old(old_names['tgt_ct'])[0],
                        gfbn_new(new_names['tgt_ct'])[0],
                    )],
                    override_uniques=(old_names['src'], old_names['tgt_fk'],
                                      old_names['tgt_ct']),
                )
                return

            # Make a new through table
            self.create_model(new_field.rel.through)
            # Copy the data across
            self.execute("INSERT INTO %s (%s) SELECT %s FROM %s" % (
                self.quote_name(new_field.rel.through._meta.db_table),
                ', '.join([
                    "id",
                    gfbn_new(old_names['src'])[0].column,
                    gfbn_new(old_names['tgt_fk'])[0].column,
                    gfbn_new(old_names['tgt_ct'])[0].column,
                ]),
                ', '.join([
                    "id",
                    gfbn_old(old_names['src'])[0].column,
                    gfbn_old(old_names['tgt_fk'])[0].column,
                    gfbn_old(old_names['tgt_ct'])[0].column,
                ]),
                self.quote_name(old_field.rel.through._meta.db_table),
            ))
            # Delete the old through table
            self.delete_model(old_field.rel.through)
        else:
            return _alter_many_to_many_sqlite0(self, model, old_field,
                                               new_field, strict)
    DatabaseSchemaEditor._alter_many_to_many = _alter_many_to_many

    from  django.db.migrations.autodetector import MigrationAutodetector

    def only_relation_agnostic_fields(self, fields):
        """
        We only change the way the 'to' key is deleted from the dict
        (as GM2MField.deconstruct does not return a 'to' kwarg)
        """
        fields_def = []
        for __, field in fields:
            deconstruction = self.deep_deconstruct(field)
            if field.rel and field.rel.to:
                deconstruction[2].pop('to', None)
            fields_def.append(deconstruction)
        return fields_def

    MigrationAutodetector.only_relation_agnostic_fields = \
        only_relation_agnostic_fields


except (ImportError, AttributeError):
    # Django < 1.7, don't worry about the migration stuff
    pass
