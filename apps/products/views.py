from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q

from .models import Category, Product, ProductImage, Wishlist, Banner
from .serializers import (
    CategorySerializer, ProductListSerializer, ProductDetailSerializer,
    ProductCreateSerializer, WishlistSerializer, BannerSerializer
)
from apps.products.filter import ProductFilter
from apps.users.permission import IsAdmin, IsSeller, IsSellerOrAdmin



class CategoryListView(generics.ListAPIView):
    serializer_class   = CategorySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Category.objects.filter(parent__isnull=True, is_active=True)



class ProductListView(generics.ListAPIView):
    serializer_class   = ProductListSerializer
    permission_classes = [permissions.AllowAny]
    filterset_class    = ProductFilter
    search_fields      = ['name', 'description', 'category__name', 'seller__shop_name']
    ordering_fields    = ['price', 'rating', 'sold_count', 'created_at']
    ordering           = ['-created_at']

    def get_queryset(self):
        return Product.objects.filter(
            is_active=True, is_approved=True
        ).select_related('seller', 'category').prefetch_related('images')


class ProductDetailView(generics.RetrieveAPIView):
    serializer_class   = ProductDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field       = 'slug'

    def get_queryset(self):
        return Product.objects.filter(
            is_active=True, is_approved=True
        ).select_related('seller', 'category').prefetch_related('images', 'variants')


class SellerProductListView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsSeller]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProductCreateSerializer
        return ProductListSerializer

    def get_queryset(self):
        return Product.objects.filter(
            seller=self.request.user.seller_profile
        ).prefetch_related('images')


class SellerProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class   = ProductCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsSeller]

    def get_queryset(self):
        return Product.objects.filter(seller=self.request.user.seller_profile)


class ProductImageUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsSeller]
    parser_classes     = [MultiPartParser, FormParser]

    def post(self, request, product_id):
        try:
            product = Product.objects.get(pk=product_id, seller=request.user.seller_profile)
        except Product.DoesNotExist:
            return Response({'detail': 'Topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        images = request.FILES.getlist('images')
        if not images:
            return Response({'detail': 'Rasm yuklanmadi'}, status=status.HTTP_400_BAD_REQUEST)

        created = []
        for i, img in enumerate(images):
            pi = ProductImage.objects.create(
                product=product, image=img,
                is_main=(i == 0 and not product.images.exists()),
                order=product.images.count() + i
            )
            created.append({'id': pi.id, 'is_main': pi.is_main})

        return Response({'uploaded': len(created), 'images': created}, status=status.HTTP_201_CREATED)




class WishlistView(generics.ListAPIView):
    serializer_class = WishlistSerializer

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user).select_related('product')


class WishlistToggleView(APIView):
    def post(self, request, product_id):
        try:
            product = Product.objects.get(pk=product_id, is_active=True, is_approved=True)
        except Product.DoesNotExist:
            return Response({'detail': 'Topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        obj, created = Wishlist.objects.get_or_create(user=request.user, product=product)
        if not created:
            obj.delete()
            return Response({'saved': False})
        return Response({'saved': True}, status=status.HTTP_201_CREATED)



class BannerListView(generics.ListAPIView):
    serializer_class   = BannerSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        from django.utils import timezone
        now = timezone.now()
        return Banner.objects.filter(
            is_active=True
        ).filter(
            Q(starts_at__isnull=True) | Q(starts_at__lte=now)
        ).filter(
            Q(ends_at__isnull=True) | Q(ends_at__gte=now)
        )

class AdminProductListView(generics.ListAPIView):
    serializer_class   = ProductListSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    filterset_class    = ProductFilter
    search_fields      = ['name', 'seller__shop_name']
    queryset           = Product.objects.all().select_related('seller', 'category')


class AdminProductApproveView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def post(self, request, pk):
        try:
            product             = Product.objects.get(pk=pk)
            product.is_approved = True
            product.save()
            from notifications.tasks import send_product_approved_notification
            send_product_approved_notification.delay(product.id)
            return Response({'detail': f'{product.name} tasdiqlandi'})
        except Product.DoesNotExist:
            return Response({'detail': 'Topilmadi'}, status=status.HTTP_404_NOT_FOUND)


class AdminPendingProductsView(generics.ListAPIView):
    serializer_class   = ProductListSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get_queryset(self):
        return Product.objects.filter(is_approved=False).select_related('seller', 'category')