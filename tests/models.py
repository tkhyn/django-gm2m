from django.db import models


class Base(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        abstract = True


class Project(Base):
    pass


class Task(Base):
    pass
