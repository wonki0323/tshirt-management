from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from orders.models import Order, OrderItem, Status
from finance.models import Expense, Purchase
from products.models import Product


@login_required
def dashboard(request):
    """홈화면 대시보드"""
    
    # CANCELED 상태가 아닌 주문만 대상으로 계산
    active_orders = Order.objects.exclude(status=Status.CANCELED)
    
    # FINANCE: 매출-매입=순이익 계산 (요구사항 10: COMPLETED 주문만)
    # 매출: 완료된 주문의 총 결제 금액
    completed_orders = Order.objects.filter(status=Status.COMPLETED)
    total_revenue = sum(
        order.total_order_amount 
        for order in completed_orders
    )
    
    # 매입: 실제 매입 내역 (재료비)
    total_purchases = sum(
        purchase.amount * purchase.quantity 
        for purchase in Purchase.objects.all()
    )
    
    # 지출: 운영비용 (공과금, 임대료 등)
    total_expenses = sum(
        expense.amount * expense.quantity 
        for expense in Expense.objects.all()
    )
    
    # 스마트스토어 수수료 (매출의 6%)
    from decimal import Decimal
    smartstore_fee = Decimal(str(total_revenue)) * Decimal('0.06')
    
    # 순이익 계산 = 매출 - 매입 - 지출 - 스마트스토어 수수료
    net_profit_with_vat = Decimal(str(total_revenue)) - Decimal(str(total_purchases)) - Decimal(str(total_expenses)) - smartstore_fee
    
    # 부가세 제외 순이익 = 순이익 / 1.1
    vat_exclusive_profit = net_profit_with_vat / Decimal('1.1')
    vat_amount = net_profit_with_vat - vat_exclusive_profit
    
    # ORDERS: 주문 상태별 개수 (요구사항 1)
    order_stats = {
        'new': Order.objects.filter(status=Status.NEW).count(),
        'consulting': Order.objects.filter(status=Status.CONSULTING).count(),
        'producing': Order.objects.filter(status=Status.PRODUCING).count(),
        'produced': Order.objects.filter(status=Status.PRODUCED).count(),
    }
    
    # PRODUCTS: 제품 개수
    total_products = Product.objects.count()
    
    context = {
        'total_revenue': total_revenue,
        'total_purchases': total_purchases,
        'total_expenses': total_expenses,
        'smartstore_fee': smartstore_fee,
        'net_profit_with_vat': net_profit_with_vat,
        'vat_amount': vat_amount,
        'vat_exclusive_profit': vat_exclusive_profit,
        'order_stats': order_stats,
        'total_products': total_products,
    }
    
    return render(request, 'dashboard.html', context)
