from django.core.signals import Signal

_del_args = ['del_objs', 'rel_objs']
deleting_src = Signal(providing_args=_del_args)
deleting_tgt = Signal(providing_args=_del_args)
