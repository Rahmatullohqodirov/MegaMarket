from django.core.cache import cache
from django.conf import settings

MAX_ATTEMPTS    = getattr(settings, 'LOGIN_MAX_ATTEMPTS', 5)
BLOCK_DURATION  = getattr(settings, 'LOGIN_BLOCK_DURATION', 300)


def get_attempt_key(phone: str) -> str:
    return f"login_attempts:{phone}"


def get_block_key(phone: str) -> str:
    return f"login_blocked:{phone}"


def is_blocked(phone: str) -> bool:
    """Hisob bloklangan ekanini tekshirish"""
    return bool(cache.get(get_block_key(phone)))


def get_block_ttl(phone: str) -> int:
    """Blok qancha vaqt qolganini qaytarish"""
    return cache.ttl(get_block_key(phone)) or 0


def increment_attempts(phone: str) -> int:
    """Urinish sonini oshirish"""
    key      = get_attempt_key(phone)
    attempts = cache.get(key, 0) + 1
    cache.set(key, attempts, timeout=BLOCK_DURATION)

    if attempts >= MAX_ATTEMPTS:
        # Bloklash
        cache.set(get_block_key(phone), True, timeout=BLOCK_DURATION)
        cache.delete(key)

    return attempts


def reset_attempts(phone: str) -> None:
    """Muvaffaqiyatli login — urinishlarni tiklash"""
    cache.delete(get_attempt_key(phone))
    cache.delete(get_block_key(phone))


def remaining_attempts(phone: str) -> int:
    """Qolgan urinishlar soni"""
    attempts = cache.get(get_attempt_key(phone), 0)
    return max(MAX_ATTEMPTS - attempts, 0)