from django.utils import six
from django.db.models.fields import Field
from django.db import connection
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from .relations import GM2MRel, REL_ATTRS

from .compat import checks, get_model_name, assert_compat_params, \
                    add_field, db_backends_utils

from . import monkeypatch


class GM2MField(Field):
    """
    Provides a generic relation to several generic objects through a
    generic model storing content-type/object-id information

    Reverse relations can be established with models provided as arguments
    """

    # field flags
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
            null=True,
        )

        assert_compat_params(params)

        self.db_table = params.pop('db_table', None)
        self.pk_maxlength = params.pop('pk_maxlength', False)
        if self.rel.through is not None:
            assert self.db_table is None and self.pk_maxlength is False, \
                'django-gm2m: Cannot specify a db_table nor a pk_maxlength ' \
                'if ''an intermediary model is used.'

    def check(self, **kwargs):
        errors = super(GM2MField, self).check(**kwargs)
        errors.extend(self._check_unique(**kwargs))
        errors.extend(self.rel.check(**kwargs))
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
        for rel in self.rel.rels:
            if getattr(rel, '_added', False):
                continue

            if isinstance(rel.to, six.string_types):
                args.append(rel.to)
            else:
                # see if the related model is a swappable model
                swappable_setting = rel.swappable_setting
                if swappable_setting is not None:
                    setting_name = getattr(rel.to, 'setting_name', None)
                    if setting_name != swappable_setting:
                        raise ValueError(
                            'Cannot deconstruct a GM2MField pointing to a '
                            'model that is swapped in place of more than one '
                            'model (%s and %s)'
                            % (setting_name, swappable_setting))

                    from django.db.migrations.writer import SettingsReference
                    to = SettingsReference(rel.to, swappable_setting)
                else:
                    to = '%s.%s' % (rel.to._meta.app_label,
                                    rel.to._meta.object_name)
                args.append(to)

        # handle parameters
        if self.db_table:
            kwargs['db_table'] = self.db_table
        if self.pk_maxlength is not False:
            kwargs['pk_maxlength'] = self.pk_maxlength

        through = self.rel.through
        if through:
            if isinstance(through, six.string_types):
                kwargs['through'] = through
            elif not through._meta.auto_created:
                kwargs['through'] = '%s.%s' % (through._meta.app_label,
                                               through._meta.object_name)

        # rel options
        for k, default in six.iteritems(REL_ATTRS):
            if k == 'through':
                # through has been dealt with just above
                continue
            value = getattr(self.rel, k)
            if value != default:
                if k == 'related_name':
                    value = force_text(value)
                kwargs[k] = value

        # on_delete options
        on_delete = kwargs.get('on_delete', REL_ATTRS['on_delete'])
        for param in ('on_delete_src', 'on_delete_tgt'):
            value = getattr(self.rel, param)
            if value != on_delete:
                kwargs[param] = value

        return name, path, args, kwargs

    def add_relation(self, model):
        rel = self.rel.add_relation(model)
        rel._added = True

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
        if self.rel.through is not None:
            return self.rel.through._meta.db_table
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
            # we need to use a custom function here, as calling
            # cls._meta.add_field would only work if GM2MField derived from
            # ManyToManyField, which, for various reasons, is not the case
            add_field(opts, self)

        self.model = cls
        self.opts = cls._meta

        # Set up related classes if relations are defined
        self.rel.contribute_to_class(cls)

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
        return self.rel.related_name and self.rel.related_name[-1] == '+'

    def related_query_name(self):
        return self.rel.related_query_name or self.rel.related_name \
            or get_model_name(self.model)
