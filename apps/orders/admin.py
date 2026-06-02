from django.contrib import admin

from apps.orders.models import Cart,CartItem,Order,OrderItem,OrderStatusLog,Return,Review
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(OrderStatusLog)
admin.site.register(Return)
admin.site.register(Review)