from django.http import JsonResponse
from django.conf import settings
from django.core.cache import cache
import ipaddress


def get_client_ip(request) -> str:
    """Mijoz haqiqiy IP sini olish"""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def ip_in_list(ip: str, ip_list: list) -> bool:
    """IP manzil ro'yxatda bormi tekshirish (CIDR qo'llab-quvvatlaydi)"""
    try:
        client = ipaddress.ip_address(ip)
        for allowed in ip_list:
            try:
                if '/' in allowed:
                    if client in ipaddress.ip_network(allowed, strict=False):
                        return True
                elif client == ipaddress.ip_address(allowed):
                    return True
            except ValueError:
                continue
    except ValueError:
        pass
    return False


class PaymentIPMiddleware:
    """Payme va Click so'rovlarini faqat ruxsat berilgan IP dan qabul qilish"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        if '/api/v1/payments/payme/' in path:
            ip      = get_client_ip(request)
            allowed = getattr(settings, 'PAYME_ALLOWED_IPS', [])
            if allowed and not ip_in_list(ip, allowed):
                return JsonResponse({'error': 'Forbidden'}, status=403)

        if '/api/v1/payments/click/' in path:
            ip      = get_client_ip(request)
            allowed = getattr(settings, 'CLICK_ALLOWED_IPS', [])
            if allowed and not ip_in_list(ip, allowed):
                return JsonResponse({'error': 'Forbidden'}, status=403)

        return self.get_response(request)


class BlockedIPMiddleware:
    """Bloklangan IP lardan so'rovlarni rad etish"""
    BLOCKED_KEY = 'blocked_ips'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip          = get_client_ip(request)
        blocked_ips = cache.get(self.BLOCKED_KEY, set())
        if ip in blocked_ips:
            return JsonResponse({'detail': 'IP bloklangan'}, status=403)
        return self.get_response(request)

    @classmethod
    def block_ip(cls, ip: str, duration: int = 3600):
        """IP ni bloklash"""
        blocked = cache.get(cls.BLOCKED_KEY, set())
        blocked.add(ip)
        cache.set(cls.BLOCKED_KEY, blocked, timeout=duration)

    @classmethod
    def unblock_ip(cls, ip: str):
        """IP blokini ochish"""
        blocked = cache.get(cls.BLOCKED_KEY, set())
        blocked.discard(ip)
        cache.set(cls.BLOCKED_KEY, blocked)