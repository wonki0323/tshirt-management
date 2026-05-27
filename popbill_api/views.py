import logging
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from orders.models import Order, Status
from .models import Deposit, CashReceipt
from . import services

logger = logging.getLogger(__name__)


def _back(request, default='popbill_dashboard'):
    """referer에 따라 컨트롤 패널 또는 대시보드로 리다이렉트"""
    ref = request.META.get('HTTP_REFERER', '')
    if 'control-panel' in ref:
        return redirect('control_panel')
    return redirect(default)


# ─── 메인 대시보드 ───

@login_required
def popbill_dashboard(request):
    """팝빌 연동 메인 대시보드 - 입금확인 + 현금영수증 통합"""
    unmatched_deposits = Deposit.objects.filter(match_status=Deposit.MatchStatus.UNMATCHED)
    recent_deposits = Deposit.objects.all()[:20]
    pending_receipts = CashReceipt.objects.filter(issue_status=CashReceipt.IssueStatus.PENDING)
    recent_receipts = CashReceipt.objects.all()[:10]

    # 결제 대기 중인 주문 (입금 매칭 대상)
    consulting_orders = Order.objects.filter(status=Status.CONSULTING).order_by('-payment_date')

    context = {
        'unmatched_deposits': unmatched_deposits,
        'recent_deposits': recent_deposits,
        'pending_receipts': pending_receipts,
        'recent_receipts': recent_receipts,
        'consulting_orders': consulting_orders,
    }
    return render(request, 'popbill_api/dashboard.html', context)


# ─── 입금확인 ───

@login_required
@require_POST
def fetch_deposits(request):
    """뱅크다 REST API로 최근 입금 내역 가져오기 + 자동매칭."""
    result = services.sync_bankda_deposits()

    if result.get('error'):
        messages.error(request, f"뱅크다 조회 실패: {result['error']}")
    else:
        messages.success(
            request,
            f"뱅크다 입금 신규 {result['new']}건 · 자동매칭 {result['matched']}건"
        )

    return _back(request)


@login_required
@require_POST
def confirm_deposit(request, pk):
    """입금 확인 처리 (매칭 승인)"""
    deposit = get_object_or_404(Deposit, pk=pk)
    deposit.confirmed_at = timezone.now()
    deposit.confirmed_by = request.user.username
    if deposit.match_status == Deposit.MatchStatus.UNMATCHED:
        deposit.match_status = Deposit.MatchStatus.MANUAL_MATCHED
    deposit.save()

    # 매칭된 주문 상태를 '제작중'으로 변경
    if deposit.matched_order and deposit.matched_order.status == Status.CONSULTING:
        deposit.matched_order.status = Status.PRODUCED
        deposit.matched_order.save()
        messages.success(
            request,
            f"{deposit.matched_order.customer_name}님 입금 확인 완료 → 제작중으로 변경"
        )
    else:
        messages.success(request, "입금 확인 완료")

    return _back(request)


@login_required
@require_POST
def match_deposit(request, pk):
    """수동 매칭 - 입금 내역에 주문 연결"""
    deposit = get_object_or_404(Deposit, pk=pk)
    order_id = request.POST.get('order_id')

    if not order_id:
        messages.error(request, "주문을 선택해주세요.")
        return _back(request)

    order = get_object_or_404(Order, pk=order_id)
    deposit.matched_order = order
    deposit.match_status = Deposit.MatchStatus.MANUAL_MATCHED
    deposit.save()
    messages.success(request, f"{order.customer_name}님 주문에 수동 매칭 완료")
    return _back(request)


@login_required
@require_POST
def ignore_deposit(request, pk):
    """입금 내역 무시 처리"""
    deposit = get_object_or_404(Deposit, pk=pk)
    deposit.match_status = Deposit.MatchStatus.IGNORED
    deposit.save()
    messages.info(request, "입금 내역을 무시 처리했습니다.")
    return _back(request)


@login_required
def get_matching_orders(request):
    """입금액에 매칭 가능한 주문 목록 반환 (AJAX)"""
    amount = request.GET.get('amount', '')
    try:
        amount = Decimal(amount)
    except Exception:
        return JsonResponse({'orders': []})

    orders = Order.objects.filter(
        status=Status.CONSULTING
    ).exclude(
        deposits__match_status__in=[
            Deposit.MatchStatus.AUTO_MATCHED,
            Deposit.MatchStatus.MANUAL_MATCHED,
        ]
    )

    # 금액 일치 우선, 이후 전체
    exact = orders.filter(total_order_amount=amount)
    others = orders.exclude(pk__in=exact)

    result = []
    for order in list(exact) + list(others):
        result.append({
            'id': order.pk,
            'customer_name': order.customer_name,
            'amount': str(order.total_order_amount),
            'date': order.payment_date.strftime('%m/%d'),
            'exact_match': str(order.total_order_amount) == str(amount),
        })

    return JsonResponse({'orders': result})


# ─── 현금영수증 ───

@login_required
def issue_receipt_form(request, order_id):
    """현금영수증 발급 폼"""
    order = get_object_or_404(Order, pk=order_id)
    existing = CashReceipt.objects.filter(order=order, issue_status='ISSUED').first()

    context = {
        'order': order,
        'existing_receipt': existing,
    }
    return render(request, 'popbill_api/issue_receipt.html', context)


@login_required
@require_POST
def issue_receipt(request, order_id):
    """현금영수증 발급 실행"""
    order = get_object_or_404(Order, pk=order_id)

    identity_type = request.POST.get('identity_type', 'BIZ_NO')
    identity_number = request.POST.get('identity_number', '').strip()
    trade_type = request.POST.get('trade_type', 'EXPENDITURE_PROOF')
    amount = request.POST.get('amount', '')

    if not identity_number:
        messages.error(request, "식별번호를 입력해주세요.")
        return redirect('issue_receipt_form', order_id=order.pk)

    try:
        amount = Decimal(amount)
    except Exception:
        amount = order.total_order_amount

    receipt = CashReceipt.objects.create(
        order=order,
        identity_type=identity_type,
        identity_number=identity_number,
        trade_type=trade_type,
        amount=amount,
    )

    result = services.issue_cash_receipt(receipt)

    if result['success']:
        messages.success(request, result['message'])
    else:
        messages.error(request, f"발급 실패: {result['message']}")

    return _back(request)


@login_required
def receipt_history(request):
    """현금영수증 발급 이력"""
    receipts = CashReceipt.objects.select_related('order').all()
    return render(request, 'popbill_api/receipt_history.html', {'receipts': receipts})


# ─── 컨트롤 패널 (팝업창) ───

@login_required
def control_panel(request):
    """컨트롤 패널 팝업 - 모든 빠른 작업 모음"""
    unmatched_deposits = Deposit.objects.filter(match_status=Deposit.MatchStatus.UNMATCHED)
    recent_matched = Deposit.objects.filter(
        match_status__in=[Deposit.MatchStatus.AUTO_MATCHED, Deposit.MatchStatus.MANUAL_MATCHED],
        confirmed_at__isnull=True,
    )[:5]
    consulting_orders = Order.objects.filter(status=Status.CONSULTING).order_by('-payment_date')[:15]
    recent_receipts = CashReceipt.objects.filter(issue_status=CashReceipt.IssueStatus.ISSUED).order_by('-issued_at')[:5]

    context = {
        'unmatched_deposits': unmatched_deposits,
        'unmatched_count': unmatched_deposits.count(),
        'recent_matched': recent_matched,
        'consulting_orders': consulting_orders,
        'recent_receipts': recent_receipts,
    }
    return render(request, 'popbill_api/control_panel.html', context)
