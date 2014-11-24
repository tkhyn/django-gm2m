from django.utils import six
from django.db.models.fields import Field

from .relations import GM2MRel, REL_ATTRS

from .compat import get_model_name, assert_compat_params, add_field


class GM2MField(Field):
    """
    Provides a generic relation to several generic objects through a
    generic model storing content-type/object-id information

    Reverse relations can be established with models provided as arguments
    """

    def __init__(self, *related_models, **params):

        super(GM2MField, self).__init__(
            verbose_name=params.pop('verbose_name', None),
            name=params.pop('name', None),
            help_text=params.pop('help_text', u''),
            error_messages=params.pop('error_messages', None)
        )

        assert_compat_params(params)

        self.rel = GM2MRel(self, related_models, **params)

        self.db_table = params.pop('db_table', None)
        if self.rel.through is not None:
            assert self.db_table is None, \
                'django-gm2m: Cannot specify a db_table if an intermediary ' \
                'model is used.'

    def deconstruct(self):
        name, path, args, kwargs = super(GM2MField, self).deconstruct()

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

    def get_reverse_path_info(self):
        linkfield = \
            self.through._meta.get_field_by_name(
                self.through._meta._field_names['src'])[0]
        return linkfield.get_reverse_path_info()

    def db_type(self, connection):
        """
        By default a GM2M field will not have a column as it relates
        columns to another table
        """
        return None

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

    def is_hidden(self):
        "Should the related object be hidden?"
        return self.rel.related_name and self.rel.related_name[-1] == '+'

    def related_query_name(self):
        return self.rel.related_query_name or self.rel.related_name \
            or get_model_name(self.rel.through)
