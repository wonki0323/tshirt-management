from django.contrib import admin
from .models import Deposit, CashReceipt


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ['transaction_date', 'depositor_name', 'amount', 'match_status', 'matched_order']
    list_filter = ['match_status']
    search_fields = ['depositor_name', 'memo']


@admin.register(CashReceipt)
class CashReceiptAdmin(admin.ModelAdmin):
    list_display = ['order', 'identity_type', 'identity_number', 'amount', 'issue_status', 'issued_at']
    list_filter = ['issue_status', 'identity_type']
    search_fields = ['identity_number', 'order__customer_name']
