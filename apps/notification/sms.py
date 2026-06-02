from celery import shared_task
import requests
from django.conf import settings


@shared_task
def send_sms_task(phone: str, message: str):
    """Eskiz orqali SMS yuborish"""
    try:
        # Token olish
        token_resp = requests.post(
            'https://notify.eskiz.uz/api/auth/login',
            data={'email': settings.ESKIZ_EMAIL, 'password': settings.ESKIZ_PASSWORD},
            timeout=10
        )
        token = token_resp.json().get('data', {}).get('token')
        if not token:
            return {'success': False, 'error': 'Token olishda xato'}

        resp = requests.post(
            'https://notify.eskiz.uz/api/message/sms/send',
            headers={'Authorization': f'Bearer {token}'},
            data={'mobile_phone': phone, 'message': message, 'from': '4546'},
            timeout=10
        )
        return {'success': True, 'response': resp.json()}
    except Exception as e:
        return {'success': False, 'error': str(e)}