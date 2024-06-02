import datetime
import traceback

from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    if isinstance(exc, PermissionDenied):
        return Response({'error': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)

    if isinstance(exc, ValidationError) and exc.detail and isinstance(exc.detail, dict):
        form_error = {k: ', '.join(v) if isinstance(v, list) else v for k, v in exc.detail.items()}
        return Response({'form_error': form_error}, status=status.HTTP_400_BAD_REQUEST)

    with open('error_log.txt', 'a') as f:
        f.write(f'TimeStamp: {datetime.datetime.now()}\n')
        if 'view' in context:
            module_name = getattr(context['view'], 'module_name', 'Create New Module')
            f.write(f'Module: {module_name}\n')
        f.write(f'Traceback: {traceback.format_exc()}\n\n')
        f.close()

    return Response({'error': 'Something Went Wrong'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_test_post_data():
    return {
        'name': 'IT',
        'employees': [
            {
                'name': '100021',
            },
            {
                'name': '100022',
            },
            {
                'name': '100023',
            },
        ]
    }
