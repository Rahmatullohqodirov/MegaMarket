import random
import string
from django.core.cache import cache
from django.conf import settings


def generate_otp(length: int = None) -> str:
    """6 xonali tasodifiy raqam"""
    length = length or getattr(settings, 'OTP_LENGTH', 6)
    return ''.join(random.choices(string.digits, k=length))


def save_otp(phone: str, otp: str) -> None:
    """OTP ni Redis'da saqlash"""
    expire = getattr(settings, 'OTP_EXPIRE_SECONDS', 120)
    key    = f"otp:{phone}"
    cache.set(key, otp, timeout=expire)


def verify_otp(phone: str, otp: str) -> bool:
    """OTP ni tekshirish va o'chirish"""
    key      = f"otp:{phone}"
    saved    = cache.get(key)
    if saved and saved == otp:
        cache.delete(key)
        return True
    return False


def get_otp_ttl(phone: str) -> int:
    """OTP qancha vaqt qolganini qaytarish (soniyada)"""
    key = f"otp:{phone}"
    ttl = cache.ttl(key)
    return max(ttl, 0)