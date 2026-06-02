from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, SellerProfile, Address
from .permission import IsSeller, IsAdmin
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    SellerProfileSerializer, SellerProfileUpdateSerializer,
    AddressSerializer, ChangePasswordSerializer
)



class RegisterView(generics.CreateAPIView):
    """Ro'yxatdan o'tish"""
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user':    UserSerializer(user).data,
            'access':  str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """Kirish"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user   = serializer.validated_data['user']
        tokens = serializer.get_tokens(user)
        return Response({
            'user':    UserSerializer(user).data,
            'access':  tokens['access'],
            'refresh': tokens['refresh'],
        })


class LogoutView(APIView):
    """Chiqish — refresh tokenni bekor qilish"""
    def post(self, request):
        try:
            refresh_token = request.data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'detail': 'Chiqish muvaffaqiyatli'})
        except Exception:
            return Response({'detail': 'Token noto\'g\'ri'}, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """Parolni o'zgartirish"""
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Parol o\'zgartirildi'})


# ─── Profile ─────────────────────────────────────────────────────────────────

class MeView(generics.RetrieveUpdateAPIView):
    """O'z profilini ko'rish va yangilash"""
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class SellerProfileView(generics.RetrieveUpdateAPIView):
    """Sotuvchi o'z profilini ko'rish/yangilash"""
    permission_classes = [permissions.IsAuthenticated, IsSeller]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return SellerProfileUpdateSerializer
        return SellerProfileSerializer

    def get_object(self):
        return self.request.user.seller_profile


class PublicSellerProfileView(generics.RetrieveAPIView):
    """Xaridor sotuvchi profilini ko'rish"""
    serializer_class   = SellerProfileSerializer
    permission_classes = [permissions.AllowAny]
    queryset           = SellerProfile.objects.filter(is_approved=True)


# ─── Address ─────────────────────────────────────────────────────────────────

class AddressListCreateView(generics.ListCreateAPIView):
    """Manzillar ro'yxati va yangi qo'shish"""
    serializer_class = AddressSerializer

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Manzilni ko'rish, yangilash, o'chirish"""
    serializer_class = AddressSerializer

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)


# ─── Admin ───────────────────────────────────────────────────────────────────

class AdminUserListView(generics.ListAPIView):
    """Admin: barcha foydalanuvchilar"""
    serializer_class   = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    queryset           = User.objects.all().order_by('-date_joined')
    filterset_fields   = ['role', 'is_active']
    search_fields      = ['phone', 'first_name', 'last_name']


class AdminSellerApproveView(APIView):
    """Admin: sotuvchini tasdiqlash"""
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def post(self, request, pk):
        try:
            profile             = SellerProfile.objects.get(pk=pk)
            profile.is_approved = True
            profile.save()
            # Celery task orqali sotuvchiga xabar yuborish
            from notifications.tasks import send_seller_approved_notification
            send_seller_approved_notification.delay(profile.user.id)
            return Response({'detail': f'{profile.shop_name} tasdiqlandi'})
        except SellerProfile.DoesNotExist:
            return Response({'detail': 'Topilmadi'}, status=status.HTTP_404_NOT_FOUND)


class AdminPendingSellersView(generics.ListAPIView):
    """Admin: tasdiqlanmagan sotuvchilar"""
    serializer_class   = SellerProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get_queryset(self):
        return SellerProfile.objects.filter(is_approved=False).select_related('user')



from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from apps.utils.opt import generate_otp, save_otp, verify_otp, get_otp_ttl
from apps.utils.login_attempts import is_blocked, increment_attempts, reset_attempts, remaining_attempts, get_block_ttl
from apps.utils.throttles import LoginThrottle, OTPThrottle, RegisterThrottle
from apps.notification.sms import send_sms_task
from .models import User
from .serializers import UserSerializer


class SendOTPView(APIView):
    """Telefonga OTP yuborish"""
    throttle_classes = [OTPThrottle]
    permission_classes = []

    def post(self, request):
        phone = request.data.get('phone', '').replace('+', '').replace(' ', '')

        if not phone or len(phone) < 9:
            return Response({'detail': 'Telefon raqam noto\'g\'ri'}, status=status.HTTP_400_BAD_REQUEST)

        # OTP hali amal qilyaptimi
        ttl = get_otp_ttl(phone)
        if ttl > 0:
            return Response({
                'detail': f'OTP allaqachon yuborilgan. {ttl} soniya kuting.',
                'retry_after': ttl
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        otp = generate_otp()
        save_otp(phone, otp)

        # SMS yuborish (Celery orqali)
        send_sms_task.delay(phone, f"Bozor.uz: tasdiqlash kodi {otp}. 2 daqiqa ichida foydalaning.")

        return Response({
            'detail': f'+{phone} raqamiga kod yuborildi',
            'expires_in': 120
        })


class VerifyOTPView(APIView):
    """OTP ni tasdiqlash va login"""
    throttle_classes   = [LoginThrottle]
    permission_classes = []

    def post(self, request):
        phone = request.data.get('phone', '').replace('+', '').replace(' ', '')
        otp   = request.data.get('otp', '').strip()

        # Bloklash tekshirish
        if is_blocked(phone):
            ttl = get_block_ttl(phone)
            return Response({
                'detail': f'Hisob vaqtincha bloklangan. {ttl} soniya kuting.',
                'blocked_for': ttl
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        if not verify_otp(phone, otp):
            attempts  = increment_attempts(phone)
            remaining = remaining_attempts(phone)
            if remaining == 0:
                return Response({
                    'detail': f'Hisob {get_block_ttl(phone)} soniyaga bloklandi.',
                    'blocked': True
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            return Response({
                'detail': f'Kod noto\'g\'ri. {remaining} ta urinish qoldi.',
                'remaining_attempts': remaining
            }, status=status.HTTP_400_BAD_REQUEST)

        # Muvaffaqiyatli — urinishlarni tiklash
        reset_attempts(phone)

        # Foydalanuvchi yaratish yoki topish
        user, created = User.objects.get_or_create(
            phone=phone,
            defaults={'is_active': True}
        )

        refresh = RefreshToken.for_user(user)
        return Response({
            'user':       UserSerializer(user).data,
            'access':     str(refresh.access_token),
            'refresh':    str(refresh),
            'is_new_user': created
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class SecureLoginView(APIView):
    """Parol + brute force himoya bilan login"""
    throttle_classes   = [LoginThrottle]
    permission_classes = []

    def post(self, request):
        from django.contrib.auth import authenticate

        phone    = request.data.get('phone', '').replace('+', '').replace(' ', '')
        password = request.data.get('password', '')

        # Bloklash tekshirish
        if is_blocked(phone):
            ttl = get_block_ttl(phone)
            return Response({
                'detail': f'Hisob bloklangan. {ttl} soniya kuting.',
                'blocked_for': ttl
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        user = authenticate(username=phone, password=password)

        if not user:
            attempts  = increment_attempts(phone)
            remaining = remaining_attempts(phone)
            if remaining == 0:
                return Response({
                    'detail': 'Hisob 5 daqiqaga bloklandi.',
                    'blocked': True
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            return Response({
                'detail': f'Telefon yoki parol noto\'g\'ri. {remaining} ta urinish qoldi.',
                'remaining_attempts': remaining
            }, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({'detail': 'Hisob bloklangan'}, status=status.HTTP_403_FORBIDDEN)

        # Muvaffaqiyatli login
        reset_attempts(phone)
        refresh = RefreshToken.for_user(user)
        return Response({
            'user':    UserSerializer(user).data,
            'access':  str(refresh.access_token),
            'refresh': str(refresh),
        })