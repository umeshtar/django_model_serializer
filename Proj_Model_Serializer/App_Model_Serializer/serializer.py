from django.core.exceptions import ImproperlyConfigured
from rest_framework.exceptions import ValidationError
from rest_framework.relations import PrimaryKeyRelatedField, ManyRelatedField
from rest_framework.serializers import ModelSerializer

from .models import Employee, Department


class DjangoSerializerValidator:

    def __init__(self, serializer, attrs):
        self.serializer = serializer
        self.data = attrs

    def get_verbose_name(self, name):
        return self.serializer.Meta.model._meta.get_field(name).verbose_name.capitalize()

    def check_empty(self, *args):
        for field in args:
            if field in self.data:
                if not self.data[field]:
                    raise ValidationError({field: f'{self.get_verbose_name(field)} is Required'})

    def check_exists(self, *args):
        for field in args:
            if field in self.data and self.data[field]:
                qs = self.serializer.Meta.model.objects.filter(**{f'{field}__icontains': self.data[field]})
                if self.serializer.instance is not None:
                    qs = qs.exclude(pk=self.serializer.instance.pk)
                if qs.exists():
                    raise ValidationError({field: f'{self.get_verbose_name(field)} Already Exists'})


class DjangoCrudModelSerializer(ModelSerializer):

    class Meta:
        model = None
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.Meta.model or not self.Meta.fields:
            raise ImproperlyConfigured(f'model or fields Missing in {self.__class__.__name__} Meta Class')

    def to_representation(self, instance):
        # is_form = self.context.get('is_form', False)
        data = super().to_representation(instance)
        data['rec_id'] = str(instance.id + 10000)
        data['salt'] = instance.salt
        for k, v in self.get_fields().items():
            if isinstance(v, PrimaryKeyRelatedField):
                inst = getattr(instance, k, None)
                if inst:
                    data[k] = {'value': str(inst.id + 10000),
                               'salt': inst.salt,
                               'label': str(inst)}
            if isinstance(v, ManyRelatedField):
                qs = getattr(instance, k, None)
                data[k] = [{'value': str(inst.id + 10000),
                            'salt': inst.salt,
                            'label': str(inst)} for inst in qs.all()]
        return data


class EmployeeSerializer(DjangoCrudModelSerializer):
    class Meta:
        model = Employee
        fields = ['name', 'department']

    def validate(self, attrs):
        dsv = DjangoSerializerValidator(self, attrs)
        dsv.check_empty('department')
        dsv.check_exists('name')
        return attrs


class DepartmentSerializer(DjangoCrudModelSerializer):
    employees = EmployeeSerializer(many=True)

    class Meta:
        model = Department
        fields = ['name', 'employees']

    def validate(self, attrs):
        dsv = DjangoSerializerValidator(self, attrs)
        dsv.check_exists('name')
        return attrs




