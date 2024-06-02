from django.contrib import admin
from django.urls import path, include

from . import views

urlpatterns = [
    path('employee/', views.EmployeeView.as_view(), name='employee'),
    path('department/', views.DepartmentView.as_view(), name='department'),
]
