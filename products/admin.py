from django.contrib import admin
from .models import Product, ProductOption


class ProductOptionInline(admin.TabularInline):
    """제품 상세 페이지에서 옵션을 인라인으로 표시"""
    model = ProductOption
    extra = 1
    fields = ['option_detail', 'base_cost', 'is_active']
    ordering = ['option_detail']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name']
    ordering = ['name']
    inlines = [ProductOptionInline]
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('name', 'category', 'is_active')
        }),
    )


@admin.register(ProductOption)
class ProductOptionAdmin(admin.ModelAdmin):
    list_display = ['product', 'option_detail', 'base_cost', 'is_active', 'created_at']
    list_filter = ['product', 'is_active', 'created_at']
    search_fields = ['product__name', 'option_detail']
    ordering = ['product', 'option_detail']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('product', 'option_detail', 'base_cost', 'is_active')
        }),
    )