"""뱅크다(Bankda) 자동입금확인 webhook endpoints (방식 A).

뱅크다가 30분~24시간 주기로 호출:
1. unconfirmed_orders_list  GET — 결제 대기 중인 주문 리스트
2. order_detail              POST — order_id로 주문 1건 상세
3. payment_confirm           POST — order_id 리스트의 입금확인 처리

인증: Cloudflare-style IP 화이트리스트 (decorator).
인증 미통과 시 401 (가이드 §401).
"""
import ipaddress
import json
import logging

from django.conf import settings
from django.db import transaction
from django.http import JsonResponse, HttpResponseNotAllowed
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from orders.models import Order, Status

logger = logging.getLogger(__name__)

# 가이드 §방화벽 (2026-05-25 화면 캡처)
BANKDA_ALLOWED_IPS = [
    ipaddress.ip_network('13.209.86.108'),
    ipaddress.ip_network('124.198.76.144/28'),
]

# 우리 IBK 받는 계좌 (BANKDA_ACCOUNT_NUM 환경변수에서 가져오되 기본은 .env)
DEFAULT_BANK_CODE_NAME = '기업은행'


def _client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def _ip_allowed(ip_str):
    if not ip_str:
        return False
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    return any(ip in net for net in BANKDA_ALLOWED_IPS)


def _unauthorized():
    return JsonResponse({'error': '인증 정보 오류'}, status=401)


def _bank_account_no():
    return (settings.BANKDA_ACCOUNT_NUM or '').strip()


def _bankda_response(data, status=200):
    """뱅크다 측 파서는 한글이 \\uXXXX escape일 때 row를 못 읽음.
    ensure_ascii=False + UTF-8 charset 명시.
    """
    return JsonResponse(
        data,
        status=status,
        json_dumps_params={'ensure_ascii': False},
        content_type='application/json; charset=utf-8',
    )


def _serialize_order(order):
    items = [
        {'product_name': item.smartstore_product_name}
        for item in order.items.all()
    ]
    # 뱅크다 자동매치 조건: 적요(송금자명) = 입금예정자명 1:1 정확 일치 필수.
    # deposit_name 있으면 그걸 사용 (자동매치 가능) / 없으면 customer_name fallback (자동매치 미작동, 수동 처리)
    deposit_name = (order.deposit_name or '').strip() or order.customer_name
    return {
        'order_id': order.smartstore_order_id,
        'buyer_name': deposit_name,
        'billing_name': deposit_name,
        'bank_account_no': _bank_account_no(),
        'bank_code_name': DEFAULT_BANK_CODE_NAME,
        'order_price_amount': int(order.total_order_amount),
        'order_date': timezone.localtime(order.payment_date).strftime('%Y-%m-%d %H:%M:%S'),
        'items': items,
    }


@csrf_exempt
def unconfirmed_orders_list(request):
    """입금확인 전 주문건 리스트. 뱅크다가 GET으로 호출."""
    if request.method not in ('GET', 'POST'):
        return HttpResponseNotAllowed(['GET', 'POST'])
    if not _ip_allowed(_client_ip(request)):
        logger.warning('bankda IP 차단: %s', _client_ip(request))
        return _unauthorized()

    from .models import Deposit

    orders_qs = (
        Order.objects
        .filter(status=Status.NEW)
        .exclude(
            deposits__match_status__in=[
                Deposit.MatchStatus.AUTO_MATCHED,
                Deposit.MatchStatus.MANUAL_MATCHED,
            ]
        )
        .prefetch_related('items')
        .order_by('-payment_date')[:100]
    )
    # 미확인주문리스트: orders 키 외 메타 항목 없어야 (테스트 검증 결과)
    return _bankda_response({
        'orders': [_serialize_order(o) for o in orders_qs],
    })


def _parse_json_body(request):
    try:
        return json.loads(request.body or b'{}')
    except (ValueError, json.JSONDecodeError):
        return None


@csrf_exempt
def order_detail(request):
    """주문 1건 상세. 뱅크다가 POST {"order_id": "..."}로 호출.

    응답은 미확인주문리스트와 같은 {"orders": [...]} 형식 (배열 길이 1).
    """
    if request.method not in ('POST', 'PUT'):
        return HttpResponseNotAllowed(['POST', 'PUT'])
    if not _ip_allowed(_client_ip(request)):
        logger.warning('bankda IP 차단: %s', _client_ip(request))
        return _unauthorized()

    body = _parse_json_body(request)
    if body is None:
        return JsonResponse({'error': 'JSON 형식 오류'}, status=400)
    order_id = (body.get('order_id') or '').strip()
    if not order_id:
        return JsonResponse({'error': 'order_id 누락'}, status=400)

    try:
        order = (
            Order.objects
            .prefetch_related('items')
            .get(smartstore_order_id=order_id)
        )
    except Order.DoesNotExist:
        return _bankda_response({'order': {}})

    # 주문상세: order는 단일 객체 (배열 X). 가설: order 안 row의 order_id를
    # 뱅크다가 배열로 박으면 못 찾고, 단일 객체로 박아야 인식.
    return _bankda_response({'order': _serialize_order(order)})


@csrf_exempt
def payment_confirm(request):
    """뱅크다가 매칭한 결과 알림.

    정책 (2026-05-27 운영자 결정): **자동 NEW→CONSULTING 이동 + 운영자 퇴근 전 롤백**.
    - Order.status NEW면 자동 CONSULTING으로 이동
    - Deposit 행에 Order 정보 채움 (입금자명·금액 등)
    - 운영자가 컨트롤 팝업에서 [되돌리기] 클릭하면 CONSULTING → NEW 복귀
    - 매칭 오류 케이스 (동명이인·외상 거래 충돌) 대응
    """
    if request.method not in ('POST', 'PUT'):
        return HttpResponseNotAllowed(['POST', 'PUT'])
    if not _ip_allowed(_client_ip(request)):
        logger.warning('bankda IP 차단: %s', _client_ip(request))
        return _unauthorized()

    from .models import Deposit
    from orders.models import Status

    body = _parse_json_body(request)
    if body is None:
        return JsonResponse({'error': 'JSON 형식 오류'}, status=400)
    requests_list = body.get('requests') or []
    if not isinstance(requests_list, list):
        return JsonResponse({'error': 'requests 배열 형식 오류'}, status=400)

    orders_resp = []
    for entry in requests_list:
        order_id = (entry or {}).get('order_id') or ''
        order_id = order_id.strip()
        if not order_id:
            orders_resp.append({'order_id': order_id, 'description': 'invalid'})
            continue

        try:
            order = Order.objects.get(smartstore_order_id=order_id)
        except Order.DoesNotExist:
            orders_resp.append({'order_id': order_id, 'description': 'not_found'})
            continue

        with transaction.atomic():
            # Deposit 행에 Order 정보 활용해서 채움.
            # confirmed_at=None — 컨트롤 팝업 "확인 대기"에 표시되어 운영자 검토 가능
            Deposit.objects.update_or_create(
                source=Deposit.Source.BANKDA,
                transaction_id=f'bankda_confirm_{order_id}',
                defaults={
                    'transaction_date': timezone.now(),
                    'depositor_name': f'(뱅크다) {order.customer_name}',
                    'amount': order.total_order_amount,
                    'matched_order': order,
                    'match_status': Deposit.MatchStatus.AUTO_MATCHED,
                    'raw_payload': entry,
                },
            )

            # Order.status NEW → CONSULTING 자동 이동
            if order.status == Status.NEW:
                order.status = Status.CONSULTING
                order.save(update_fields=['status'])

        orders_resp.append({'order_id': order_id, 'description': 'OK'})

    return _bankda_response({
        'return_code': '200',
        'description': 'OK',
        'orders': orders_resp,
    })


@csrf_exempt
def rollback_deposit(request, pk):
    """잘못 자동매칭된 Deposit 되돌리기 — Order.status CONSULTING → NEW.

    운영자가 컨트롤 팝업의 [되돌리기] 버튼 클릭 시.
    Django 세션 인증 (운영자 로그인 상태).
    """
    from django.contrib.auth.decorators import login_required
    from django.views.decorators.http import require_POST
    from django.shortcuts import get_object_or_404, redirect

    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'login required'}, status=401)

    from .models import Deposit
    from orders.models import Status

    deposit = get_object_or_404(Deposit, pk=pk, source=Deposit.Source.BANKDA)

    with transaction.atomic():
        if deposit.matched_order and deposit.matched_order.status == Status.CONSULTING:
            deposit.matched_order.status = Status.NEW
            deposit.matched_order.save(update_fields=['status'])
        deposit.match_status = Deposit.MatchStatus.IGNORED
        deposit.confirmed_at = None
        deposit.confirmed_by = ''
        deposit.save(update_fields=['match_status', 'confirmed_at', 'confirmed_by'])

    ref = request.META.get('HTTP_REFERER', '')
    if 'control-panel' in ref:
        return redirect('control_panel')
    return redirect('popbill_dashboard')
