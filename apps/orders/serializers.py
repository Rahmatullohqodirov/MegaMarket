from rest_framework import serializers
from django.db import transaction
from .models import Cart, CartItem, Order, OrderItem, Return, Review
from apps.products.models import Product
from apps.products.serializers import ProductListSerializer


# ─── Cart ────────────────────────────────────────────────────────────────────

class CartItemSerializer(serializers.ModelSerializer):
    product  = ProductListSerializer(read_only=True)
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model  = CartItem
        fields = ('id', 'product', 'variant', 'quantity', 'subtotal')


class CartSerializer(serializers.ModelSerializer):
    items      = CartItemSerializer(many=True, read_only=True)
    total      = serializers.ReadOnlyField()
    item_count = serializers.ReadOnlyField()

    class Meta:
        model  = Cart
        fields = ('id', 'items', 'total', 'item_count', 'updated_at')


class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    variant_id = serializers.IntegerField(required=False, allow_null=True)
    quantity   = serializers.IntegerField(min_value=1, default=1)

    def validate_product_id(self, value):
        try:
            product = Product.objects.get(pk=value, is_active=True, is_approved=True)
            if not product.in_stock:
                raise serializers.ValidationError('Mahsulot stokda yo\'q')
            return value
        except Product.DoesNotExist:
            raise serializers.ValidationError('Mahsulot topilmadi')


# ─── Order ───────────────────────────────────────────────────────────────────

class OrderItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model  = OrderItem
        fields = ('id', 'name', 'price', 'quantity', 'subtotal', 'is_reviewed')


class OrderListSerializer(serializers.ModelSerializer):
    items_count = serializers.SerializerMethodField()
    grand_total = serializers.ReadOnlyField()

    class Meta:
        model  = Order
        fields = ('id', 'order_number', 'status', 'total_amount', 'grand_total', 'items_count', 'created_at')

    def get_items_count(self, obj):
        return obj.items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    items       = OrderItemSerializer(many=True, read_only=True)
    grand_total = serializers.ReadOnlyField()

    class Meta:
        model  = Order
        fields = (
            'id', 'order_number', 'status', 'total_amount', 'delivery_cost',
            'discount_amount', 'grand_total', 'shipping_address', 'note',
            'items', 'created_at', 'updated_at', 'completed_at'
        )


class CreateOrderSerializer(serializers.Serializer):
    address_id = serializers.IntegerField()
    promo_code = serializers.CharField(required=False, allow_blank=True)
    note       = serializers.CharField(required=False, allow_blank=True)

    def validate_address_id(self, value):
        from users.models import Address
        try:
            return Address.objects.get(pk=value, user=self.context['request'].user)
        except Address.DoesNotExist:
            raise serializers.ValidationError('Manzil topilmadi')

    @transaction.atomic
    def create_order(self, user):
        from payments.models import PromoCode
        from django.conf import settings

        cart = Cart.objects.get(user=user)
        if not cart.items.exists():
            raise serializers.ValidationError('Savatcha bo\'sh')

        address  = self.validated_data['address_id']
        promo    = None
        discount = 0

        # Promo kod tekshirish
        promo_code = self.validated_data.get('promo_code', '')
        if promo_code:
            try:
                promo    = PromoCode.objects.get(code=promo_code, is_active=True)
                discount = cart.total * promo.discount_percent / 100
            except PromoCode.DoesNotExist:
                pass

        # Buyurtma yaratish
        order = Order.objects.create(
            user=user,
            total_amount=cart.total,
            delivery_cost=15000,
            discount_amount=discount,
            promo_code=promo,
            note=self.validated_data.get('note', ''),
            shipping_address={
                'city':     address.city,
                'district': address.district,
                'street':   address.street,
            }
        )

        # OrderItem yaratish + stock kamaytirish
        for cart_item in cart.items.select_related('product', 'variant').all():
            product = cart_item.product
            price   = cart_item.variant.price if cart_item.variant and cart_item.variant.price else product.price

            # Stock tekshirish (lock bilan)
            prod = Product.objects.select_for_update().get(pk=product.pk)
            if prod.stock < cart_item.quantity:
                raise serializers.ValidationError(f'{prod.name} yetarli emas')
            prod.stock -= cart_item.quantity
            prod.save(update_fields=['stock'])

            OrderItem.objects.create(
                order    = order,
                product  = product,
                seller   = product.seller,
                variant  = cart_item.variant,
                name     = product.name,
                price    = price,
                quantity = cart_item.quantity,
            )

        cart.items.all().delete()
        return order


# ─── Return ───────────────────────────────────────────────────────────────────

class ReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Return
        fields = ('id', 'order_item', 'reason', 'description', 'status', 'created_at')
        read_only_fields = ('id', 'status', 'created_at')


# ─── Review ───────────────────────────────────────────────────────────────────

class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model  = Review
        fields = ('id', 'user_name', 'rating', 'text', 'created_at')
        read_only_fields = ('id', 'user_name', 'created_at')

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError('Reyting 1 dan 5 gacha bo\'lishi kerak')
        return value

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)