import random
import time

from django.db import models


# Create your models here.
class MyManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().filter(is_del=False)


class AllObjectsManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset()


class MyModel(models.Model):
    salt = models.CharField(max_length=100, null=True, blank=True)
    is_del = models.BooleanField(default=False)
    objects = MyManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.salt:
            self.salt = f"{time.time()}{random.random()}"
        super().save(*args, **kwargs)


class Employee(MyModel):
    name = models.CharField(max_length=100)
    department = models.ForeignKey('Department', on_delete=models.CASCADE, null=True,
                                   blank=True, related_name='employees')

    def __str__(self):
        return self.name


class Department(MyModel):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name







