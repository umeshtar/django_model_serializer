import inspect

from django.core.exceptions import ImproperlyConfigured
from rest_framework.exceptions import ValidationError
from rest_framework.relations import PrimaryKeyRelatedField, ManyRelatedField
from rest_framework.serializers import ModelSerializer

from .models import Employee, Department


class DjangoSerializerValidator:
    error_msg = {
        'check_empty': '{field} is required',
        'check_exists': '{field} is already exists',
    }

    def __init__(self, model, instance):
        self.model = model
        self.instance = instance
        self.attrs = None
        self.enc_attrs = dict()
        self.custom_errors = dict()

    def set_attrs(self, attrs):
        self.attrs = attrs

    def get_verbose_name(self, name):
        return self.model._meta.get_field(name).verbose_name.capitalize()

    def add_error(self, field):
        func_name = inspect.stack()[1].frame.f_code.co_name
        error_msg = self.error_msg[func_name].format(field=self.get_verbose_name(field))
        if field not in self.custom_errors:
            self.custom_errors[field] = [error_msg]
        else:
            self.custom_errors[field].append(error_msg)

    def check_empty(self, *args):
        for field in args:
            value = self.attrs.get(field, None)
            if not value or (isinstance(value, str) and not value.strip()):
                self.add_error(field)

    def check_exists(self, *args):
        for field in args:
            value = self.attrs.get(field, None)
            if value:
                qs = self.model.objects.filter(**{f'{field}__icontains': value})
                if self.instance is not None:
                    qs = qs.exclude(pk=self.instance.pk)
                if qs.exists():
                    self.add_error(field)


class DjangoCrudModelSerializer(ModelSerializer):

    class Meta:
        model = None
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sv = DjangoSerializerValidator(model=self.Meta.model, instance=self.instance)
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

    def save(self, **kwargs):
        if self.sv.enc_attrs:
            kwargs.update(self.sv.enc_attrs)
        return super().save(**kwargs)


class DjangoCreateUpdateModelSerializer(ModelSerializer):

    class Meta:
        model = None
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sv = DjangoSerializerValidator(model=self.Meta.model, instance=self.instance)
        if not self.Meta.model or not self.Meta.fields:
            raise ImproperlyConfigured(f'model or fields Missing in {self.__class__.__name__} Meta Class')

    def save(self, **kwargs):
        if self.sv.enc_attrs:
            kwargs.update(self.sv.enc_attrs)
        return super().save(**kwargs)


class DjangoListRetrieveModelSerializer(ModelSerializer):

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


class EmployeeCreateUpdateSerializer(DjangoCreateUpdateModelSerializer):
    class Meta:
        model = Employee
        fields = ['name', 'department']

    def validate(self, attrs):
        self.sv.set_attrs(attrs)
        self.sv.check_empty('department')
        self.sv.check_exists('name')
        if self.sv.custom_errors:
            raise ValidationError(self.sv.custom_errors)
        return attrs


class DepartmentCreateUpdateSerializer(DjangoCreateUpdateModelSerializer):

    class Meta:
        model = Department
        fields = ['name']

    def validate(self, attrs):
        self.sv.set_attrs(attrs)
        self.sv.check_exists('name')
        if self.sv.custom_errors:
            raise ValidationError(self.sv.custom_errors)
        return attrs


class EmployeeListRetrieveSerializer(DjangoListRetrieveModelSerializer):
    class Meta:
        model = Employee
        fields = ['name', 'department']


class DepartmentListRetrieveSerializer(DjangoListRetrieveModelSerializer):
    employees = EmployeeListRetrieveSerializer(many=True)

    class Meta:
        model = Department
        fields = ['name', 'employees']



