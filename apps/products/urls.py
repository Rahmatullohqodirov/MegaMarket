from django.urls import path
from . import views

urlpatterns = [
    # Kategoriyalar
    path('categories/', views.CategoryListView.as_view(), name='categories'),

    # Mahsulotlar (ommaviy)
    path('',                    views.ProductListView.as_view(),   name='products'),
    path('<slug:slug>/',        views.ProductDetailView.as_view(), name='product_detail'),

    # Sotuvchi
    path('my/',                      views.SellerProductListView.as_view(),       name='my_products'),
    path('my/<int:pk>/',             views.SellerProductDetailView.as_view(),     name='my_product_detail'),
    path('my/<int:product_id>/images/', views.ProductImageUploadView.as_view(),  name='product_images'),

    # Wishlist
    path('wishlist/',                   views.WishlistView.as_view(),            name='wishlist'),
    path('wishlist/<int:product_id>/',  views.WishlistToggleView.as_view(),      name='wishlist_toggle'),

    # Bannerlar
    path('banners/', views.BannerListView.as_view(), name='banners'),

    # Admin
    path('admin/all/',                    views.AdminProductListView.as_view(),    name='admin_products'),
    path('admin/pending/',                views.AdminPendingProductsView.as_view(), name='pending_products'),
    path('admin/<int:pk>/approve/',       views.AdminProductApproveView.as_view(), name='approve_product'),
]