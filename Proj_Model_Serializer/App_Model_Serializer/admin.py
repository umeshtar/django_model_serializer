from django.contrib import admin

from .models import *


# Register your models here.
class MyAdmin(admin.ModelAdmin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.list_display = ('id',) + self.list_display + ('is_del',)
        self.list_filter = self.list_filter + ('is_del',)

    def get_queryset(self, request):
        qs = self.model.all_objects.get_queryset()
        ordering = self.ordering or ()
        if ordering:
            qs = qs.order_by(*ordering)
        return qs


@admin.register(Employee)
class EmployeeAdmin(MyAdmin):
    list_display = ('name', 'department')


@admin.register(Department)
class DepartmentAdmin(MyAdmin):
    list_display = ('name',)







