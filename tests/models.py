from django.db import models

import gm2m

# no tests here
__test__ = False


class Base(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        abstract = True


class Project(Base):
    pass


class Task(Base):
    pass


class Links(models.Model):
    related_objects = gm2m.GM2MField()
