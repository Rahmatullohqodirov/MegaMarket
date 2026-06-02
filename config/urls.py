from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/',          include('apps.users.urls')),
    path('api/v1/products/',      include('apps.products.urls')),
    path('api/v1/orders/',        include('apps.orders.urls')),
    path('api/v1/payments/',      include('apps.payments.urls')),
    path('api/v1/notifications/', include('apps.notification.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)