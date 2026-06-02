from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class LoginThrottle(AnonRateThrottle):
    """Login uchun: minutiga 5 ta urinish"""
    scope = 'login'


class OTPThrottle(AnonRateThrottle):
    """OTP yuborish uchun: minutiga 3 ta"""
    scope = 'otp'


class RegisterThrottle(AnonRateThrottle):
    """Ro'yxatdan o'tish: soatiga 10 ta"""
    scope = 'register'


class PaymentThrottle(UserRateThrottle):
    """To'lov: soatiga 20 ta"""
    scope = 'payment'