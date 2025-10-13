from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem, Status


class OrderItemInline(admin.TabularInline):
    """주문 상세 페이지에서 주문 항목을 인라인으로 표시"""
    model = OrderItem
    extra = 0
    fields = [
        'smartstore_product_name', 
        'product_option', 
        'quantity', 
        'unit_price', 
        'unit_cost',
        'display_total_price',
        'display_total_cost',
        'display_profit'
    ]
    readonly_fields = ['display_total_price', 'display_total_cost', 'display_profit']
    ordering = ['id']

    def display_total_price(self, obj):
        """총 판매 가격"""
        if obj.pk:
            return f"{obj.total_price:,}원"
        return "-"
    display_total_price.short_description = "총 판매가"

    def display_total_cost(self, obj):
        """총 원가"""
        if obj.pk:
            return f"{obj.total_cost:,}원"
        return "-"
    display_total_cost.short_description = "총 원가"

    def display_profit(self, obj):
        """순이익"""
        if obj.pk:
            profit_amount = obj.profit
            color = "green" if profit_amount >= 0 else "red"
            return format_html(
                '<span style="color: {};">{}</span>',
                color,
                f'{profit_amount:,}원'
            )
        return "-"
    display_profit.short_description = "순이익"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'smartstore_order_id', 
        'customer_name', 
        'status', 
        'payment_date', 
        'due_date',
        'total_order_amount',
        'display_total_cost',
        'display_profit'
    ]
    list_filter = ['status', 'payment_date']
    search_fields = ['smartstore_order_id', 'customer_name', 'customer_phone']
    ordering = ['-payment_date']
    inlines = [OrderItemInline]
    readonly_fields = ['display_total_cost', 'display_profit']
    
    fieldsets = (
        ('주문 정보', {
            'fields': ('smartstore_order_id', 'status', 'payment_date')
        }),
        ('고객 정보', {
            'fields': ('customer_name', 'customer_phone', 'shipping_address')
        }),
        ('금액 정보', {
            'fields': ('total_order_amount', 'display_total_cost', 'display_profit')
        }),
        ('진행 상황', {
            'fields': ('confirmed_date', 'due_date', 'google_drive_folder_url')
        }),
    )

    def display_total_cost(self, obj):
        """주문의 총 원가"""
        if obj.pk:
            return f"{obj.total_cost:,}원"
        return "-"
    display_total_cost.short_description = "총 원가"

    def display_profit(self, obj):
        """주문의 순이익"""
        if obj.pk:
            profit_amount = obj.profit
            color = "green" if profit_amount >= 0 else "red"
            return format_html(
                '<span style="color: {};">{}</span>',
                color,
                f'{profit_amount:,}원'
            )
        return "-"
    display_profit.short_description = "순이익"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = [
        'order', 
        'smartstore_product_name', 
        'product_option',
        'quantity', 
        'unit_price', 
        'unit_cost',
        'display_total_price',
        'display_total_cost',
        'display_profit'
    ]
    list_filter = ['created_at']
    search_fields = [
        'order__smartstore_order_id', 
        'smartstore_product_name', 
        'smartstore_option_text'
    ]
    ordering = ['-created_at', 'id']
    readonly_fields = ['display_total_price', 'display_total_cost', 'display_profit']
    
    fieldsets = (
        ('주문 정보', {
            'fields': ('order',)
        }),
        ('제품 정보', {
            'fields': ('product_option', 'smartstore_product_name', 'smartstore_option_text')
        }),
        ('수량 및 가격', {
            'fields': ('quantity', 'unit_price', 'unit_cost')
        }),
        ('계산 결과', {
            'fields': ('display_total_price', 'display_total_cost', 'display_profit')
        }),
        ('기타', {
            'fields': ('design_image_url',)
        }),
    )

    def display_total_price(self, obj):
        """총 판매 가격"""
        if obj.pk:
            return f"{obj.total_price:,}원"
        return "-"
    display_total_price.short_description = "총 판매가"

    def display_total_cost(self, obj):
        """총 원가"""
        if obj.pk:
            return f"{obj.total_cost:,}원"
        return "-"
    display_total_cost.short_description = "총 원가"

    def display_profit(self, obj):
        """순이익"""
        if obj.pk:
            profit_amount = obj.profit
            color = "green" if profit_amount >= 0 else "red"
            return format_html(
                '<span style="color: {};">{}</span>',
                color,
                f'{profit_amount:,}원'
            )
        return "-"
    display_profit.short_description = "순이익"