from django.db import models

import gm2m
from gm2m.deletion import CASCADE, DO_NOTHING_SIGNAL

from ..app.models import Task


# we establish the link with Task before declaring the Milestone
class Links(models.Model):

    class Meta:
        app_label = 'inheritancedel'

    related_objects = gm2m.GM2MField(Task, on_delete_src=CASCADE,
                                     on_delete_tgt=DO_NOTHING_SIGNAL)


class Subtask(Task):

    class Meta:
        proxy = True
        app_label = 'inheritancedel'


class Milestone(Task):

    class Meta:
        app_label = 'inheritancedel'
