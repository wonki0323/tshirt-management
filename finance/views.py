from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Sum, Q
from decimal import Decimal
from .models import Expense, Purchase
from .forms import ExpenseForm, PurchaseForm
from orders.models import Order, Status


def calculate_income_tax(taxable_income):
    """
    종합소득세 계산 (2023-2024년 귀속)
    산출세액 = (과세표준 × 해당구간세율) - 누진공제액
    """
    from decimal import Decimal
    
    # Decimal로 변환
    if not isinstance(taxable_income, Decimal):
        taxable_income = Decimal(str(taxable_income))
    
    # 과세표준 구간 및 세율 (모두 Decimal로 처리)
    tax_brackets = [
        (Decimal('14000000'), Decimal('0.06'), Decimal('0')),                    # 1,400만원 이하: 6%
        (Decimal('50000000'), Decimal('0.15'), Decimal('1260000')),              # 1,400만원 초과 ~ 5,000만원 이하: 15%, 누진공제 126만원
        (Decimal('88000000'), Decimal('0.24'), Decimal('5760000')),              # 5,000만원 초과 ~ 8,800만원 이하: 24%, 누진공제 576만원
        (Decimal('150000000'), Decimal('0.35'), Decimal('15440000')),            # 8,800만원 초과 ~ 1억 5,000만원 이하: 35%, 누진공제 1,544만원
        (Decimal('300000000'), Decimal('0.38'), Decimal('19940000')),            # 1억 5,000만원 초과 ~ 3억원 이하: 38%, 누진공제 1,994만원
        (Decimal('500000000'), Decimal('0.40'), Decimal('25940000')),            # 3억원 초과 ~ 5억원 이하: 40%, 누진공제 2,594만원
        (Decimal('1000000000'), Decimal('0.42'), Decimal('35940000')),           # 5억원 초과 ~ 10억원 이하: 42%, 누진공제 3,594만원
        (Decimal('9999999999999'), Decimal('0.45'), Decimal('65940000')),        # 10억원 초과: 45%, 누진공제 6,594만원
    ]
    
    for limit, rate, deduction in tax_brackets:
        if taxable_income <= limit:
            tax = taxable_income * rate - deduction
            return int(tax) if tax > 0 else 0
    
    return 0


@login_required
def financial_summary(request):
    """재무 요약 및 세금 계산"""
    from datetime import datetime
    
    # 필터 파라미터
    year = request.GET.get('year', datetime.now().year)
    month = request.GET.get('month', '')
    include_smartstore_fee = request.GET.get('include_smartstore_fee', 'true') == 'true'
    
    try:
        year = int(year)
    except:
        year = datetime.now().year
    
    # 기본 쿼리셋
    orders_query = Order.objects.filter(
        payment_date__year=year,
        status=Status.COMPLETED
    )
    purchases_query = Purchase.objects.filter(date__year=year)
    expenses_query = Expense.objects.filter(date__year=year)
    
    # 월 필터
    if month:
        try:
            month = int(month)
            orders_query = orders_query.filter(payment_date__month=month)
            purchases_query = purchases_query.filter(date__month=month)
            expenses_query = expenses_query.filter(date__month=month)
        except:
            pass
    
    # 매출 계산 (완료된 주문의 총 금액)
    total_revenue = orders_query.aggregate(
        total=Sum('total_order_amount')
    )['total'] or Decimal('0')
    
    # 매입 계산 (총 매입 금액 = amount × quantity)
    total_purchase = Decimal('0')
    for purchase in purchases_query:
        total_purchase += purchase.total_amount
    
    # 지출 계산 (총 지출 금액 = amount × quantity)
    total_expense = Decimal('0')
    for expense in expenses_query:
        total_expense += expense.total_amount
    
    # 스마트스토어 수수료 계산 (매출의 6%)
    smartstore_fee = Decimal('0')
    if include_smartstore_fee:
        smartstore_fee = total_revenue * Decimal('0.06')
    
    # 순이익 계산 = 매출 - 매입 - 지출 - 스마트스토어 수수료
    net_profit = total_revenue - total_purchase - total_expense - smartstore_fee
    
    # 부가세 계산 = 순이익 / 1.1 (부가세 10%)
    vat_exclusive_profit = net_profit / Decimal('1.1')
    vat_amount = net_profit - vat_exclusive_profit
    
    # 종합소득세 계산 (부가세 제외한 순이익 기준)
    income_tax = calculate_income_tax(vat_exclusive_profit)
    
    # 실수령액 = 순이익 - 부가세 - 종합소득세
    net_income = vat_exclusive_profit - Decimal(str(income_tax))
    
    context = {
        'year': year,
        'month': month,
        'include_smartstore_fee': include_smartstore_fee,
        'total_revenue': total_revenue,
        'total_purchase': total_purchase,
        'total_expense': total_expense,
        'smartstore_fee': smartstore_fee,
        'net_profit': net_profit,
        'vat_amount': vat_amount,
        'vat_exclusive_profit': vat_exclusive_profit,
        'income_tax': income_tax,
        'net_income': net_income,
        'revenue_count': orders_query.count(),
        'purchase_count': purchases_query.count(),
        'expense_count': expenses_query.count(),
    }
    
    return render(request, 'finance/financial_summary.html', context)


@login_required
def net_profit_summary(request):
    """순이익 요약 (부가세 제외)"""
    from datetime import datetime
    
    # 필터 파라미터
    year = request.GET.get('year', datetime.now().year)
    month = request.GET.get('month', datetime.now().month)
    include_smartstore_fee = request.GET.get('include_smartstore_fee', 'true') == 'true'
    
    try:
        year = int(year)
    except:
        year = datetime.now().year
    
    try:
        month = int(month) if month else datetime.now().month
    except:
        month = datetime.now().month
    
    # 기본 쿼리셋
    orders_query = Order.objects.filter(
        payment_date__year=year,
        payment_date__month=month,
        status=Status.COMPLETED
    ).exclude(status=Status.CANCELED)
    
    purchases_query = Purchase.objects.filter(
        date__year=year,
        date__month=month
    )
    
    expenses_query = Expense.objects.filter(
        date__year=year,
        date__month=month
    )
    
    # 매출 계산
    total_revenue = Decimal('0')
    for order in orders_query:
        total_revenue += order.total_order_amount
    
    # 매입 계산 (총 매입 금액 = amount × quantity)
    total_purchase = Decimal('0')
    for purchase in purchases_query:
        total_purchase += purchase.total_amount
    
    # 지출 계산 (총 지출 금액 = amount × quantity)
    total_expense = Decimal('0')
    for expense in expenses_query:
        total_expense += expense.total_amount
    
    # 스마트스토어 수수료 계산 (매출의 6%)
    smartstore_fee = Decimal('0')
    if include_smartstore_fee:
        smartstore_fee = total_revenue * Decimal('0.06')
    
    # 순이익 계산 = 매출 - 매입 - 지출 - 스마트스토어 수수료
    net_profit = total_revenue - total_purchase - total_expense - smartstore_fee
    
    # 부가세 계산 = 순이익 / 1.1 (부가세 10%)
    vat_exclusive_profit = net_profit / Decimal('1.1')
    vat_amount = net_profit - vat_exclusive_profit
    
    context = {
        'year': year,
        'month': month,
        'include_smartstore_fee': include_smartstore_fee,
        'total_revenue': total_revenue,
        'total_purchase': total_purchase,
        'total_expense': total_expense,
        'smartstore_fee': smartstore_fee,
        'net_profit': net_profit,
        'vat_amount': vat_amount,
        'vat_exclusive_profit': vat_exclusive_profit,
    }
    
    return render(request, 'finance/net_profit_summary.html', context)


class ExpenseListView(LoginRequiredMixin, ListView):
    """지출 목록"""
    model = Expense
    template_name = 'finance/expense_list.html'
    context_object_name = 'expenses'
    paginate_by = 20
    ordering = ['-date']


class ExpenseCreateView(LoginRequiredMixin, CreateView):
    """지출 등록"""
    model = Expense
    form_class = ExpenseForm
    template_name = 'finance/expense_form.html'
    success_url = reverse_lazy('expense_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '지출 등록'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, '지출이 성공적으로 등록되었습니다.')
        return super().form_valid(form)


class ExpenseDeleteView(LoginRequiredMixin, DeleteView):
    """지출 삭제"""
    model = Expense
    template_name = 'finance/expense_confirm_delete.html'
    success_url = reverse_lazy('expense_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, '지출이 삭제되었습니다.')
        return super().delete(request, *args, **kwargs)


class PurchaseListView(LoginRequiredMixin, ListView):
    """매입 목록"""
    model = Purchase
    template_name = 'finance/purchase_list.html'
    context_object_name = 'purchases'
    paginate_by = 20
    ordering = ['-date']


class PurchaseCreateView(LoginRequiredMixin, CreateView):
    """매입 등록"""
    model = Purchase
    form_class = PurchaseForm
    template_name = 'finance/purchase_form.html'
    success_url = reverse_lazy('purchase_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '매입 등록'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, '매입이 성공적으로 등록되었습니다.')
        return super().form_valid(form)


class PurchaseDeleteView(LoginRequiredMixin, DeleteView):
    """매입 삭제"""
    model = Purchase
    template_name = 'finance/purchase_confirm_delete.html'
    success_url = reverse_lazy('purchase_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, '매입이 삭제되었습니다.')
        return super().delete(request, *args, **kwargs)
