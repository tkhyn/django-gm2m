from django.core.signals import Signal

# providing args:
# - ``del_objs``, objects being deleted in the first place
# - ``rel_objs``, related object for cascade deletion
deleting = Signal()
