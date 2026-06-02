from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """Barcha xatolarni bir xil formatda qaytarish"""
    response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            'success': False,
            'status_code': response.status_code,
            'errors': {}
        }

        if isinstance(response.data, dict):
            # detail xabari
            if 'detail' in response.data:
                error_data['message'] = str(response.data['detail'])
            else:
                error_data['message'] = 'Xato yuz berdi'
                error_data['errors']  = response.data
        elif isinstance(response.data, list):
            error_data['message'] = str(response.data[0])
        else:
            error_data['message'] = str(response.data)

        response.data = error_data

    return response
