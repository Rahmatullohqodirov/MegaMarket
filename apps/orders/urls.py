from django.urls import path
from . import views

urlpatterns = [
    path('cart/',                   views.CartView.as_view(),       name='cart'),
    path('cart/items/',             views.CartItemView.as_view(),   name='cart_add'),
    path('cart/items/<int:item_id>/', views.CartItemView.as_view(), name='cart_item'),

    path('',              views.OrderListView.as_view(),   name='orders'),
    path('create/',       views.CreateOrderView.as_view(), name='order_create'),
    path('<int:pk>/',     views.OrderDetailView.as_view(), name='order_detail'),
    path('<int:pk>/cancel/', views.CancelOrderView.as_view(), name='order_cancel'),

    path('returns/', views.ReturnCreateView.as_view(), name='return_create'),

    # Izohlar
    path('reviews/<int:product_id>/', views.ProductReviewListView.as_view(), name='product_reviews'),
    path('reviews/create/',           views.ReviewCreateView.as_view(),      name='review_create'),

    path('seller/', views.SellerOrderListView.as_view(), name='seller_orders'),

    path('admin/',                        views.AdminOrderListView.as_view(),   name='admin_orders'),
    path('admin/<int:pk>/status/',        views.AdminOrderStatusView.as_view(), name='admin_order_status'),
]