from django.contrib import admin

from .models import *


# Register your models here.
class MyAdmin(admin.ModelAdmin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.list_display = ('id',) + self.list_display + ('is_del',)
        self.list_filter = self.list_filter + ('is_del',)


@admin.register(Employee)
class EmployeeAdmin(MyAdmin):
    list_display = ('name',)


@admin.register(Department)
class DepartmentAdmin(MyAdmin):
    list_display = ('name',)







