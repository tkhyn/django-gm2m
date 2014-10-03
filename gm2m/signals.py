from django.core.signals import Signal

deleting = Signal(providing_args=['del_objs', 'rel_objs'])
