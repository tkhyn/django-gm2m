from django.utils import six
from django.db.models.fields import Field
from django.db import connection
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.core import checks
from django.db.backends import utils as db_backends_utils

from .relations import GM2MRel, REL_ATTRS, REL_ATTRS_NAMES


class GM2MField(Field):
    """
    Provides a generic relation to several generic objects through a
    generic model storing content-type/object-id information

    Reverse relations can be established with models provided as arguments
    """

    # Field flags
    auto_created = False
    concrete = False
    editable = False
    hidden = False

    is_relation = True
    many_to_many = True
    many_to_one = False
    one_to_many = False
    one_to_one = False

    related_model = ''

    description = _('Generic many-to-many relationship')

    def __init__(self, *related_models, **params):

        super(GM2MField, self).__init__(
            verbose_name=params.pop('verbose_name', None),
            name=params.pop('name', None),
            help_text=params.pop('help_text', u''),
            error_messages=params.pop('error_messages', None),
            rel=GM2MRel(self, related_models, **params),
            # setting null to True only prevent makemigrations from asking for
            # a default value
            null=True
        )

        self.db_table = params.pop('db_table', None)
        self.pk_maxlength = params.pop('pk_maxlength', False)
        if self.remote_field.through is not None:
            assert self.db_table is None and self.pk_maxlength is False, \
                'django-gm2m: Cannot specify a db_table nor a pk_maxlength ' \
                'if ''an intermediary model is used.'

    def check(self, **kwargs):
        errors = super(GM2MField, self).check(**kwargs)
        errors.extend(self._check_unique(**kwargs))
        errors.extend(self.remote_field.check(**kwargs))
        return errors

    def _check_unique(self, **kwargs):
        if self.unique:
            return [
                checks.Error(
                    'GM2MFields cannot be unique.',
                    hint=None,
                    obj=self,
                    id='gm2m.E001',
                )
            ]
        return []

    def deconstruct(self):
        name, path, args, kwargs = super(GM2MField, self).deconstruct()

        kwargs.pop('null', None)

        # generate related models list (cannot get it from rel, as it can
        # be changed by add_relation)
        for rel in self.remote_field.rels:
            if getattr(rel, '_added', False):
                continue

            if isinstance(rel.model, six.string_types):
                args.append(rel.model)
            else:
                # see if the related model is a swappable model
                swappable_setting = rel.swappable_setting
                if swappable_setting is not None:
                    setting_name = getattr(rel.model, 'setting_name', None)
                    if setting_name != swappable_setting:
                        raise ValueError(
                            'Cannot deconstruct a GM2MField pointing to a '
                            'model that is swapped in place of more than one '
                            'model (%s and %s)'
                            % (setting_name, swappable_setting))

                    from django.db.migrations.writer import SettingsReference
                    model = SettingsReference(rel.model, swappable_setting)
                else:
                    model = '%s.%s' % (rel.model._meta.app_label,
                                    rel.model._meta.object_name)
                args.append(model)

        # handle parameters
        if self.db_table:
            kwargs['db_table'] = self.db_table
        if self.pk_maxlength is not False:
            kwargs['pk_maxlength'] = self.pk_maxlength

        through = self.remote_field.through
        if through:
            if isinstance(through, six.string_types):
                kwargs['through'] = through
            elif not through._meta.auto_created:
                kwargs['through'] = '%s.%s' % (through._meta.app_label,
                                               through._meta.object_name)

        # rel options
        for k in REL_ATTRS_NAMES:
            if k == 'through':
                # through has been dealt with just above
                continue

            # retrieve default value
            try:
                default = REL_ATTRS[k]
            except KeyError:
                if k.startswith('on_delete_'):
                    default = kwargs.get('on_delete', REL_ATTRS['on_delete'])
                else:
                    # this is a fixed attribute, we don't need to care about it
                    continue

            # retrieve actual initial value, possibly from _init_attr dict
            try:
                value = self.remote_field._init_attrs[k]
            except KeyError:
                value = getattr(self.remote_field, k)

            if value != default:
                if k == 'related_name':
                    value = force_text(value)
                kwargs[k] = value

        return name, path, args, kwargs

    def add_relation(self, model, auto=False):
        rel = self.remote_field.add_relation(model, auto=auto)
        rel._added = True

    def get_related_models(self, include_auto=False):
        models = []
        for unitrel in self.remote_field.rels:
            if not unitrel.auto or include_auto:
                models.append(unitrel.model)
        return models

    def db_type(self, connection):
        """
        A GM2M field will not have a column as it defines a relation between
        tables
        """
        return None

    def get_internal_type(self):
        """
        A GM2M field behaves like a ManyToManyField
        """
        # For Django 1.7
        return 'ManyToManyField'

    def m2m_db_table(self):
        # self.db_table will be None if
        if self.remote_field.through is not None:
            return self.remote_field.through._meta.db_table
        elif self.db_table:
            return self.db_table
        else:
            return db_backends_utils.truncate_name(
                '%s_%s' % (self.model._meta.db_table, self.name),
                connection.ops.max_name_length())

    def contribute_to_class(self, cls, name, virtual_only=False):
        """
        Appends accessor to a class and create intermediary model

        :param cls: the class to contribute to
        :param name: the name of the accessor
        """
        self.set_attributes_from_name(name)
        self.model = cls

        opts = cls._meta
        if virtual_only:
            opts.add_virtual_field(self)
        else:
            opts.add_field(self)
            # we need to clear the options cache here. It would automatically
            # be done by add_field above if GM2MField derived from
            # ManyToManyField, but for various reasons it is not the case
            opts._expire_cache()

        self.model = cls
        self.opts = cls._meta

        # Set up related classes if relations are defined
        self.remote_field.contribute_to_class(cls)

    def get_attname_column(self):
        """
        A GM2M field will not have a column as it defines a relation between
        tables
        """
        attname = self.get_attname()
        return attname, None

    def is_hidden(self):
        """
        Should the related object be hidden?
        """
        return self.remote_field.related_name \
            and self.remote_field.related_name[-1] == '+'

    def related_query_name(self):
        return self.remote_field.related_query_name \
            or self.remote_field.related_name \
            or self.model._meta.model_name
