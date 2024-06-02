from django.db.models import Prefetch
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Employee, Department
from .serializer import EmployeeSerializer, DepartmentSerializer


class GenericAPICrudView(GenericAPIView):
    model = None
    form_configs = None
    module_name = 'Create New Module'

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
        action = self.request.GET.get('action', None)
        if action == 'fetch_record':
            return {'pk': int(self.request.GET['rec_id']) - 10000}
        if self.request.method == 'PUT' and 'rec_id' in self.request.GET:
            return {'pk': int(self.request.GET['rec_id']) - 10000}
        return dict()
    
    def get_queryset(self):
        return self.model.objects.all()

    def get_object(self):
        return self.get_queryset().get(**self.get_object_lookup_kwargs())

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
            response['data'] = self.serializer_class(self.get_queryset(), many=True).data
        if action == 'fetch_record':
            response['data'] = self.serializer_class(self.get_object()).data
        if request.GET.get('get_form_configs', False) is True:
            response['form_configs'] = self.get_form_configs()
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        s = self.serializer_class(data=self.get_post_data())
        s.is_valid(raise_exception=True)
        s.save()
        return Response({'success': s.data}, status=status.HTTP_201_CREATED)

    def put(self, request, *args, **kwargs):
        s = self.serializer_class(data=self.get_post_data(), instance=self.get_object())
        s.is_valid(raise_exception=True)
        s.save()
        return Response({'success': s.data}, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        self.get_object().delete()


class EmployeeView(GenericAPICrudView):
    model = Employee
    serializer_class = EmployeeSerializer


class DepartmentView(GenericAPICrudView):
    model = Department
    serializer_class = DepartmentSerializer

    def get_queryset(self):
        return self.model.objects.prefetch_related(
            Prefetch('employees', queryset=Employee.objects.all())
        ).all()





