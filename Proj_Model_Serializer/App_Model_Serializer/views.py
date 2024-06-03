from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.response import Response

from .models import Employee, Department
from .serializer import EmployeeListRetrieveSerializer, EmployeeCreateUpdateSerializer, \
    DepartmentListRetrieveSerializer, DepartmentCreateUpdateSerializer
from .utils import get_test_post_data


class GenericAPICRUDView(GenericAPIView):
    model = None
    form_configs = None
    list_serializer_class = None
    module_name = 'Create New Module'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.model is None:
            raise ImproperlyConfigured(f"Attribute 'model' missing in {self.__class__.__name__}")

    def get_list_serializer(self, *args, **kwargs):
        if self.list_serializer_class:
            return self.list_serializer_class(*args, **kwargs)
        return self.get_serializer(*args, **kwargs)
    
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
            response['data'] = self.get_list_serializer(self.get_queryset(), many=True).data
        if action == 'fetch_record':
            response['data'] = self.get_list_serializer(self.get_object()).data
        if request.GET.get('get_form_configs', False) is True:
            response['form_configs'] = self.get_form_configs()
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        if hasattr(self, 'repeaters') and hasattr(self, 'repeater_instance_key'):
            try:
                with transaction.atomic():
                    form_errors = dict()
                    data = get_test_post_data()
                    repeater_data = dict()
                    for repeater in self.repeaters:
                        repeater_data[repeater] = data.pop(repeater, [])
                    s = self.get_serializer(data=self.get_post_data(post_data=data))
                    s.is_valid(raise_exception=True)
                    inst = s.save()
                    for repeater in self.repeaters:
                        for index, post_data in enumerate(repeater_data[repeater]):
                            post_data = self.get_post_data(post_data=post_data, serializer_class=self.repeaters[repeater])
                            post_data[self.repeater_instance_key] = inst.pk
                            s = self.repeaters[repeater](data=post_data)
                            if s.is_valid():
                                s.save()
                            else:
                                form_errors.update({f'{repeater}.{index}.{k}': v for k, v in s.errors.items()})
                    if form_errors:
                        raise ValidationError(form_errors)
                    return Response({'success': s.data}, status=status.HTTP_201_CREATED)
            except:
                transaction.rollback()
                raise
        return self.create_or_update()

    def put(self, request, *args, **kwargs):
        return self.create_or_update(instance=self.get_object())

    def create_or_update(self, instance=None):
        s = self.get_serializer(data=self.get_post_data(), instance=instance)
        s.is_valid(raise_exception=True)
        inst = s.save()
        status_code = status.HTTP_200_OK if instance else status.HTTP_201_CREATED
        return Response({'success': self.get_list_serializer(inst).data}, status=status_code)

    def delete(self, request, *args, **kwargs):
        self.get_object().delete()
        return Response({'success': 'Deleted'}, status=status.HTTP_200_OK)


class EmployeeView(GenericAPICRUDView):
    model = Employee
    serializer_class = EmployeeCreateUpdateSerializer
    list_serializer_class = EmployeeListRetrieveSerializer


class DepartmentView(GenericAPICRUDView):
    model = Department
    serializer_class = DepartmentCreateUpdateSerializer
    list_serializer_class = DepartmentListRetrieveSerializer
    repeater_instance_key = 'department'
    repeaters = {
        'employees': EmployeeCreateUpdateSerializer,
    }

    def get_queryset(self):
        return self.model.objects.prefetch_related('employees').all()


