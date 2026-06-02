import django_filters
from .models import Product


class ProductFilter(django_filters.FilterSet):

    price_min = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='price', lookup_expr='lte')

    rating_min = django_filters.NumberFilter(field_name='rating', lookup_expr='gte')

    in_stock = django_filters.BooleanFilter(method='filter_in_stock')

    has_discount = django_filters.BooleanFilter(method='filter_has_discount')

    class Meta:
        model  = Product
        fields = ['category', 'seller', 'is_approved', 'price_min', 'price_max', 'rating_min']

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock__gt=0)
        return queryset.filter(stock=0)

    def filter_has_discount(self, queryset, name, value):
        if value:
            return queryset.filter(old_price__isnull=False)
        return queryset.filter(old_price__isnull=True)