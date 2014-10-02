from django.core.signals import Signal

deleting_src = Signal(providing_args=['objs'])
deleting_tgt = Signal(providing_args=['objs'])
