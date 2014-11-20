
from django.db.models.deletion import CASCADE, DO_NOTHING
from django.utils import six

from .signals import deleting


__all__ = ['CASCADE', 'DO_NOTHING', 'CASCADE_SIGNAL', 'CASCADE_SIGNAL_VETO',
           'DO_NOTHING_SIGNAL', 'handlers_with_signal', 'handlers_do_nothing']


def collector_data_iterator(data):
    for __, instances in six.iteritems(data):
        for instance in instances:
            yield instance


def CASCADE_SIGNAL(collector, field, sub_objs, using):
    deleting.send(field, del_objs=collector_data_iterator(collector.data),
                  rel_objs=sub_objs)
    CASCADE(collector, field, sub_objs, using)


def CASCADE_SIGNAL_VETO(collector, field, sub_objs, using):
    res = deleting.send(field,
                        del_objs=collector_data_iterator(collector.data),
                        rel_objs=sub_objs)
    if not any(r[1] for r in res):
        # if no receiver returned a truthy result (veto), we can
        # cascade-collect, else we do nothing
        CASCADE(collector, field, sub_objs, using)


def DO_NOTHING_SIGNAL(collector, field, sub_objs, using):
    deleting.send(field, del_objs=collector_data_iterator(collector.data),
                  rel_objs=sub_objs)


handlers_do_nothing = (DO_NOTHING, DO_NOTHING_SIGNAL)
handlers_with_signal = (CASCADE_SIGNAL, CASCADE_SIGNAL_VETO, DO_NOTHING_SIGNAL)
