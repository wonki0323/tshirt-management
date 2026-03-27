from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from orders.models import Order, OrderItem, Status
from finance.models import Expense, Purchase
from products.models import Product


@login_required
def dashboard(request):
    """홈화면 대시보드"""
    from django.utils import timezone
    from datetime import datetime
    from decimal import Decimal
    
    # 이번 달 기준 설정 (1일 ~ 말일)
    now = timezone.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # 다음 달 1일 계산 후 -1초 하는 방식 또는 __year, __month 필터 사용
    
    # CANCELED 상태가 아닌 주문만 대상으로 계산
    active_orders = Order.objects.exclude(status=Status.CANCELED)
    
    # FINANCE: 이번 달 매출-매입=순이익 계산
    # 매출: 매출현황(sales_status)과 동일 — 결제 이후 상태, 이번 달 payment_date 기준 (등록/취소 제외)
    monthly_revenue_orders = Order.objects.filter(
        Q(status=Status.CONSULTING)
        | Q(status=Status.PRODUCED)
        | Q(status=Status.COMPLETED)
        | Q(status=Status.SETTLED)
        | Q(status=Status.ARCHIVED),
        payment_date__year=now.year,
        payment_date__month=now.month,
    )
    total_revenue = monthly_revenue_orders.aggregate(
        total=Sum('total_order_amount')
    )['total'] or Decimal('0')
    
    # 매입: 이번 달 매입 내역
    purchases = Purchase.objects.filter(
        date__year=now.year,
        date__month=now.month
    )
    total_purchases = sum(
        purchase.amount * purchase.quantity 
        for purchase in purchases
    )
    
    # 지출: 이번 달 지출 내역
    expenses = Expense.objects.filter(
        date__year=now.year,
        date__month=now.month
    )
    total_expenses = sum(
        expense.amount * expense.quantity 
        for expense in expenses
    )
    
    # 스마트스토어 수수료 (매출의 6%)
    smartstore_fee = Decimal(str(total_revenue)) * Decimal('0.06')
    
    # 순이익 계산 = 매출 - 매입 - 지출 - 스마트스토어 수수료
    net_profit_with_vat = Decimal(str(total_revenue)) - Decimal(str(total_purchases)) - Decimal(str(total_expenses)) - smartstore_fee
    
    # 부가세 제외 순이익 = 순이익 / 1.1
    vat_exclusive_profit = net_profit_with_vat / Decimal('1.1')
    vat_amount = net_profit_with_vat - vat_exclusive_profit
    
    # ORDERS: 주문 상태별 개수 (전체 누적 - 처리해야 할 건수이므로)
    order_stats = {
        'new': Order.objects.filter(status=Status.NEW).count(),
        'consulting': Order.objects.filter(status=Status.CONSULTING).count(),
        'produced': Order.objects.filter(status=Status.PRODUCED).count(),
    }
    
    # 전체 진행중 주문 (취소·발송 완료·결과통보·정산 목록 제외)
    total_orders = Order.objects.exclude(
        status__in=[
            Status.CANCELED,
            Status.COMPLETED,
            Status.SETTLED,
            Status.ARCHIVED,
        ]
    ).count()
    
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
        'total_orders': total_orders,
        'total_products': total_products,
        'current_month_str': f"{now.year}년 {now.month}월",
    }
    
    return render(request, 'dashboard.html', context)
