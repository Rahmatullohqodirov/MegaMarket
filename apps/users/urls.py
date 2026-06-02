from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Auth
    path('register/',        views.RegisterView.as_view(),       name='register'),
    path('login/',           views.LoginView.as_view(),          name='login'),
    path('logout/',          views.LogoutView.as_view(),         name='logout'),
    path('token/refresh/',   TokenRefreshView.as_view(),         name='token_refresh'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),

    # Profile
    path('me/',             views.MeView.as_view(),              name='me'),
    path('seller/profile/', views.SellerProfileView.as_view(),   name='seller_profile'),
    path('sellers/<int:pk>/', views.PublicSellerProfileView.as_view(), name='public_seller'),

    # Addresses
    path('addresses/',        views.AddressListCreateView.as_view(), name='address_list'),
    path('addresses/<int:pk>/', views.AddressDetailView.as_view(),   name='address_detail'),

    # Admin
    path('admin/users/',               views.AdminUserListView.as_view(),      name='admin_users'),
    path('admin/sellers/pending/',     views.AdminPendingSellersView.as_view(), name='pending_sellers'),
    path('admin/sellers/<int:pk>/approve/', views.AdminSellerApproveView.as_view(), name='approve_seller'),
]