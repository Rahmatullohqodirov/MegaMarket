from rest_framework import serializers
from .models import Category, Product, ProductImage, ProductVariant, Wishlist, Banner
from apps.users.serializers import SellerProfileSerializer


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model  = Category
        fields = ('id', 'name', 'slug', 'image', 'parent', 'children', 'order')

    def get_children(self, obj):
        if obj.children.exists():
            return CategorySerializer(obj.children.filter(is_active=True), many=True).data
        return []


class CategoryMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Category
        fields = ('id', 'name', 'slug')


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ProductImage
        fields = ('id', 'image', 'is_main', 'order')


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ProductVariant
        fields = ('id', 'color', 'size', 'stock', 'price')


class ProductListSerializer(serializers.ModelSerializer):
    main_image       = serializers.SerializerMethodField()
    seller_name      = serializers.CharField(source='seller.shop_name', read_only=True)
    category_name    = serializers.CharField(source='category.name', read_only=True)
    discount_percent = serializers.ReadOnlyField()
    in_stock         = serializers.ReadOnlyField()

    class Meta:
        model  = Product
        fields = (
            'id', 'name', 'slug', 'price', 'old_price', 'discount_percent',
            'rating', 'review_count', 'sold_count', 'in_stock',
            'main_image', 'seller_name', 'category_name', 'created_at'
        )

    def get_main_image(self, obj):
        img = obj.images.filter(is_main=True).first() or obj.images.first()
        if img:
            request = self.context.get('request')
            return request.build_absolute_uri(img.image.url) if request else img.image.url
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variants  = ProductVariantSerializer(many=True, read_only=True)
    seller = SellerProfileSerializer(read_only=True)
    category = CategoryMiniSerializer(read_only=True)
    discount_percent = serializers.ReadOnlyField()
    in_stock = serializers.ReadOnlyField()

    class Meta:
        model  = Product
        fields = (
            'id', 'name', 'slug', 'description', 'price', 'old_price',
            'discount_percent', 'stock', 'in_stock', 'rating', 'review_count',
            'sold_count', 'images', 'variants', 'seller', 'category',
            'is_approved', 'created_at', 'updated_at'
        )


class ProductCreateSerializer(serializers.ModelSerializer):
    """Sotuvchi mahsulot qo'shganda"""
    images   = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, required=False)

    class Meta:
        model  = Product
        fields = ('id', 'name', 'description', 'price', 'old_price', 'stock', 'category', 'images', 'variants')

    def create(self, validated_data):
        variants_data = validated_data.pop('variants', [])
        product = Product.objects.create(
            seller=self.context['request'].user.seller_profile,
            **validated_data
        )
        for v in variants_data:
            ProductVariant.objects.create(product=product, **v)
        return product


class WishlistSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)

    class Meta:
        model  = Wishlist
        fields = ('id', 'product', 'created_at')


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Banner
        fields = ('id', 'title', 'image', 'link', 'position', 'order')
