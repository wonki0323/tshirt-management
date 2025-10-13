from django.contrib import admin
from django.utils.html import format_html
from .models import Expense, Purchase


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = [
        'date', 
        'category', 
        'description_short', 
        'amount', 
        'quantity',
        'total_amount'
    ]
    list_filter = ['category', 'date', 'created_at']
    search_fields = ['description']
    ordering = ['-date', '-created_at']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('date', 'category', 'description')
        }),
        ('금액 정보', {
            'fields': ('amount', 'quantity', 'total_amount')
        }),
    )
    readonly_fields = ['total_amount']

    def description_short(self, obj):
        """설명을 50자로 제한하여 표시"""
        if obj.description:
            return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
        return "-"
    description_short.short_description = "설명"

    def total_amount(self, obj):
        """총 지출 금액"""
        if obj.pk:
            return f"{obj.total_amount:,}원"
        return "-"
    total_amount.short_description = "총 지출금액"


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = [
        'date', 
        'category', 
        'description_short', 
        'amount', 
        'quantity',
        'total_amount'
    ]
    list_filter = ['category', 'date', 'created_at']
    search_fields = ['description']
    ordering = ['-date', '-created_at']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('date', 'category', 'description')
        }),
        ('금액 정보', {
            'fields': ('amount', 'quantity', 'total_amount')
        }),
    )
    readonly_fields = ['total_amount']

    def description_short(self, obj):
        """설명을 50자로 제한하여 표시"""
        if obj.description:
            return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
        return "-"
    description_short.short_description = "설명"

    def total_amount(self, obj):
        """총 매입 금액"""
        if obj.pk:
            return f"{obj.total_amount:,}원"
        return "-"
    total_amount.short_description = "총 매입금액"