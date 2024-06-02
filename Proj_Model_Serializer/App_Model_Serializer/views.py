from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.response import Response

from .models import Employee, Department
from .serializer import EmployeeSerializer, DepartmentSerializer
from .utils import get_test_post_data


class GenericAPICrudView(GenericAPIView):
    model = None
    form_configs = None
    module_name = 'Create New Module'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.model is None:
            raise ImproperlyConfigured(f"Attribute 'model' missing in {self.__class__.__name__}")

    def get_form_configs(self):
        return self.form_configs

    def get_post_data(self, post_data=None, serializer_class=None):
        post_data = post_data or self.request.data
        serializer_class = serializer_class or self.get_serializer_class()
        post_data = post_data.copy()
        for k, v in serializer_class().get_fields().items():
            if k in post_data and post_data[k] and isinstance(v, PrimaryKeyRelatedField):
                post_data[k] = int(post_data[k]) - 10000
        return post_data
    
    def get_object_lookup_kwargs(self):
        return {'pk': int(self.request.GET['rec_id']) - 10000}
    
    def get_queryset(self):
        return self.model.objects.all()

    def get_object(self):
        return self.get_queryset().get(**self.get_object_lookup_kwargs())

    def get_serializer_context(self):
        context = super().get_serializer_context()
        action = self.request.GET.get('action', None)
        if action == 'fetch_record' and self.request.GET.get('is_form', False) == 'True':
            context['is_form'] = True
        return context

    def get(self, request, *args, **kwargs):
        """
        Allowed Cases to Call this method
        1. Listing of Data from Queryset, action: get_data
        2. Retrieving Single Object for Displaying Data, action: fetch_record
        3. Retrieving Single Object for Editing Form, action: fetch_record, is_form: True
        4. Getting Form Configuration for React Hook Form, get_form_configs: True
        """
        action = request.GET.get('action', None)
        response = {'data': None}
        if action == 'get_data':
            response['data'] = self.get_serializer(self.get_queryset(), many=True).data
        if action == 'fetch_record':
            response['data'] = self.get_serializer(self.get_object()).data
        if request.GET.get('get_form_configs', False) is True:
            response['form_configs'] = self.get_form_configs()
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        s = self.get_serializer(data=self.get_post_data())
        s.is_valid(raise_exception=True)
        s.save()
        return Response({'success': s.data}, status=status.HTTP_201_CREATED)

    def put(self, request, *args, **kwargs):
        s = self.get_serializer(data=self.get_post_data(), instance=self.get_object())
        s.is_valid(raise_exception=True)
        s.save()
        return Response({'success': s.data}, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        self.get_object().delete()
        return Response({'success': 'Deleted'}, status=status.HTTP_200_OK)


class EmployeeView(GenericAPICrudView):
    model = Employee
    serializer_class = EmployeeSerializer


class DepartmentView(GenericAPICrudView):
    model = Department
    serializer_class = DepartmentSerializer

    def get_queryset(self):
        return self.model.objects.prefetch_related('employees').all()

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                form_errors = dict()
                data = get_test_post_data()
                employees = data.pop('employees', [])
                s = self.get_serializer(data=self.get_post_data(post_data=data))
                s.is_valid(raise_exception=True)
                dept = s.save()
                for index, post_data in enumerate(employees):
                    post_data = self.get_post_data(post_data=post_data, serializer_class=EmployeeSerializer)
                    post_data['department'] = dept.pk
                    s = EmployeeSerializer(data=post_data)
                    if s.is_valid():
                        s.save()
                    else:
                        form_errors.update({f'employees.{index}.{k}': v for k, v in s.errors.items()})
                if form_errors:
                    raise ValidationError(form_errors)
                return Response({'success': s.data}, status=status.HTTP_201_CREATED)
        except:
            transaction.rollback()
            raise
        return Response({'success': s.data}, status=status.HTTP_201_CREATED)



