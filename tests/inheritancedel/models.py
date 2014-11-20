import django
from django.db.models import Model

import gm2m
from gm2m.deletion import CASCADE, DO_NOTHING_SIGNAL

from ..app.models import Task

# for Django < 1.6, the on_delete kwarg should NOT be provided
# The deletion tests are then skipped
if django.VERSION < (1, 6):
    params = {}
else:
    params = {'on_delete_src': CASCADE, 'on_delete_tgt': DO_NOTHING_SIGNAL}


# we establish the link with Task before declaring the Milestone
class Links(Model):
    related_objects = gm2m.GM2MField(Task, **params)


class Subtask(Task):
    class Meta:
        proxy = True


class Milestone(Task):
    pass
