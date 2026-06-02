from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User, SellerProfile, Address



class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = ('phone', 'first_name', 'last_name', 'password', 'password2', 'role')

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password': 'Parollar mos emas'})
        if data.get('role') == 'admin':
            raise serializers.ValidationError({'role': 'Admin roli tanlash mumkin emas'})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        if user.role == 'seller':
            SellerProfile.objects.create(user=user, shop_name=f"{user.full_name} Shop")
        return user


class LoginSerializer(serializers.Serializer):
    phone    = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['phone'], password=data['password'])
        if not user:
            raise serializers.ValidationError('Telefon yoki parol noto\'g\'ri')
        if not user.is_active:
            raise serializers.ValidationError('Hisob bloklangan')
        data['user'] = user
        return data

    def get_tokens(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access':  str(refresh.access_token),
        }


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=6)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Eski parol noto\'g\'ri')
        return value

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model  = User
        fields = ('id', 'phone', 'email', 'first_name', 'last_name', 'full_name', 'role', 'avatar', 'date_joined')
        read_only_fields = ('id', 'phone', 'role', 'date_joined')


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ('id', 'full_name', 'phone', 'avatar')


class SellerProfileSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)

    class Meta:
        model  = SellerProfile
        fields = ('id', 'user', 'shop_name', 'description', 'logo', 'balance', 'is_approved', 'rating', 'total_sales', 'created_at')
        read_only_fields = ('id', 'balance', 'is_approved', 'rating', 'total_sales', 'created_at')


class SellerProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = SellerProfile
        fields = ('shop_name', 'description', 'logo')



class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Address
        fields = ('id', 'title', 'city', 'district', 'street', 'latitude', 'longitude', 'is_default', 'created_at')
        read_only_fields = ('id', 'created_at')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)