from django.contrib import admin

from apps.products.models import Product,ProductImage,Wishlist,Banner, ProductVariant,Category

admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(Banner)
admin.site.register(ProductVariant)
admin.site.register(Category)
admin.site.register(Wishlist)