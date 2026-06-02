from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Cart, CartItem, Order, OrderItem, Return, Review, OrderStatusLog
from .serializers import (
    CartSerializer, AddToCartSerializer, CreateOrderSerializer,
    OrderListSerializer, OrderDetailSerializer, ReturnSerializer, ReviewSerializer
)
from apps.products.models import Product
from apps.users.permission import IsAdmin, IsSeller
from apps.notification.tasks import send_order_status_notification



class CartView(APIView):
    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return Response(CartSerializer(cart).data)


class CartItemView(APIView):
    def post(self, request):

        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        cart, _    = Cart.objects.get_or_create(user=request.user)
        product    = Product.objects.get(pk=data['product_id'])
        variant_id = data.get('variant_id')

        item, created = CartItem.objects.get_or_create(
            cart=cart, product=product,
            variant_id=variant_id,
            defaults={'quantity': data['quantity']}
        )
        if not created:
            item.quantity += data['quantity']
            item.save()

        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)

    def delete(self, request, item_id):
        try:
            cart = Cart.objects.get(user=request.user)
            CartItem.objects.get(pk=item_id, cart=cart).delete()
            return Response({'detail': 'O\'chirildi'})
        except (Cart.DoesNotExist, CartItem.DoesNotExist):
            return Response({'detail': 'Topilmadi'}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, item_id):
        quantity = request.data.get('quantity', 1)
        try:
            cart = Cart.objects.get(user=request.user)
            item = CartItem.objects.get(pk=item_id, cart=cart)
            if quantity <= 0:
                item.delete()
                return Response({'detail': 'O\'chirildi'})
            item.quantity = quantity
            item.save()
            return Response(CartSerializer(cart).data)
        except (Cart.DoesNotExist, CartItem.DoesNotExist):
            return Response({'detail': 'Topilmadi'}, status=status.HTTP_404_NOT_FOUND)



class OrderListView(generics.ListAPIView):
    serializer_class = OrderListSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items')


class OrderDetailView(generics.RetrieveAPIView):
    """Bitta buyurtma detail"""
    serializer_class = OrderDetailSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items')


class CreateOrderView(APIView):
    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        try:
            order = serializer.create_order(request.user)
            send_order_status_notification.delay(order.id, 'new_order')
            return Response(OrderDetailSerializer(order).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CancelOrderView(APIView):
    def post(self, request, pk):
        try:
            order = Order.objects.get(pk=pk, user=request.user)
            if order.status != 'pending':
                return Response({'detail': 'Bekor qilib bo\'lmaydi'}, status=status.HTTP_400_BAD_REQUEST)
            order.status = 'cancelled'
            order.save()
            for item in order.items.all():
                if item.product:
                    item.product.stock += item.quantity
                    item.product.save(update_fields=['stock'])
            send_order_status_notification.delay(order.id, 'cancelled')
            return Response({'detail': 'Bekor qilindi'})
        except Order.DoesNotExist:
            return Response({'detail': 'Topilmadi'}, status=status.HTTP_404_NOT_FOUND)



class ReturnCreateView(generics.CreateAPIView):
    serializer_class = ReturnSerializer

    def perform_create(self, serializer):
        order_item = serializer.validated_data['order_item']
        if order_item.order.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied()
        serializer.save()


class ProductReviewListView(generics.ListAPIView):
    serializer_class   = ReviewSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Review.objects.filter(product_id=self.kwargs['product_id']).select_related('user')


class ReviewCreateView(generics.CreateAPIView):
    serializer_class = ReviewSerializer

    def perform_create(self, serializer):
        order_item_id = self.request.data.get('order_item_id')
        try:
            item = OrderItem.objects.get(
                pk=order_item_id, order__user=self.request.user,
                order__status='completed', is_reviewed=False
            )
        except OrderItem.DoesNotExist:
            from rest_framework.exceptions import ValidationError
            raise ValidationError('Izoh qoldirishga ruxsat yo\'q')
        review = serializer.save(user=self.request.user, product=item.product, order_item=item)
        item.is_reviewed = True
        item.save()




class SellerOrderListView(generics.ListAPIView):
    serializer_class   = OrderListSerializer
    permission_classes = [permissions.IsAuthenticated, IsSeller]

    def get_queryset(self):
        return Order.objects.filter(
            items__seller=self.request.user.seller_profile
        ).distinct().prefetch_related('items')



class AdminOrderListView(generics.ListAPIView):
    serializer_class   = OrderListSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    filterset_fields   = ['status']
    search_fields      = ['order_number', 'user__phone']
    queryset           = Order.objects.all().select_related('user').prefetch_related('items')


class AdminOrderStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    ALLOWED_TRANSITIONS = {
        'pending':   ['confirmed', 'cancelled'],
        'confirmed': ['warehouse', 'cancelled'],
        'warehouse': ['shipped'],
        'shipped':   ['delivered'],
        'delivered': ['completed', 'returned'],
    }

    def post(self, request, pk):
        try:
            order      = Order.objects.get(pk=pk)
            new_status = request.data.get('status')
            allowed    = self.ALLOWED_TRANSITIONS.get(order.status, [])

            if new_status not in allowed:
                return Response({
                    'detail': f'{order.status} dan {new_status} ga o\'tib bo\'lmaydi'
                }, status=status.HTTP_400_BAD_REQUEST)

            order.status = new_status
            if new_status == 'completed':
                from django.utils import timezone
                order.completed_at = timezone.now()
                # Sotuvchi balansini to'ldirish
                from payments.tasks import process_seller_payment
                process_seller_payment.delay(order.id)

            order.save()
            OrderStatusLog.objects.create(
                order=order, status=new_status,
                created_by=request.user,
                note=request.data.get('note', '')
            )
            send_order_status_notification.delay(order.id, new_status)
            return Response({'detail': f'Holat {new_status} ga o\'zgartirildi'})

        except Order.DoesNotExist:
            return Response({'detail': 'Topilmadi'}, status=status.HTTP_404_NOT_FOUND)