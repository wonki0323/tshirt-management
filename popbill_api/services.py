"""입금확인·현금영수증 서비스 레이어. 입금확인은 뱅크다 REST API 사용."""
import logging
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


def get_popbill_config():
    """팝빌 설정값 반환"""
    return {
        'link_id': getattr(settings, 'POPBILL_LINK_ID', 'TESTER'),
        'secret_key': getattr(settings, 'POPBILL_SECRET_KEY', 'SwWxqU+0TErBXy/9TVjIPEnI0VTUMMSQZtJf3Ed8q3T='),
        'is_test': getattr(settings, 'POPBILL_IS_TEST', True),
        'corp_num': getattr(settings, 'POPBILL_CORP_NUM', ''),
        'bank_code': getattr(settings, 'POPBILL_BANK_CODE', ''),
        'account_number': getattr(settings, 'POPBILL_ACCOUNT_NUMBER', ''),
    }


def _get_easyfinbank_service():
    """팝빌 계좌조회 서비스 인스턴스 반환"""
    try:
        from popbill import EasyFinBankService
    except ImportError:
        logger.error("popbill 패키지가 설치되지 않았습니다. pip install popbill")
        return None

    config = get_popbill_config()
    service = EasyFinBankService(config['link_id'], config['secret_key'])
    service.IsTest = config['is_test']
    service.IPRestrictOnOff = False
    service.UseStaticIP = False
    service.UseLocalTimeYN = True
    return service


def _get_cashreceipt_service():
    """팝빌 현금영수증 서비스 인스턴스 반환"""
    try:
        from popbill import CashReceiptService
    except ImportError:
        logger.error("popbill 패키지가 설치되지 않았습니다. pip install popbill")
        return None

    config = get_popbill_config()
    service = CashReceiptService(config['link_id'], config['secret_key'])
    service.IsTest = config['is_test']
    service.IPRestrictOnOff = False
    service.UseStaticIP = False
    service.UseLocalTimeYN = True
    return service


# ─── 계좌조회 (입금확인) ───

def fetch_recent_deposits(days=1):
    """최근 N일간의 입금 내역을 팝빌에서 조회하여 DB에 저장

    Returns:
        dict: {'new_count': int, 'total_fetched': int, 'error': str or None}
    """
    from .models import Deposit

    service = _get_easyfinbank_service()
    if not service:
        return {'new_count': 0, 'total_fetched': 0, 'error': 'popbill 패키지 미설치'}

    config = get_popbill_config()
    if not config['corp_num']:
        return {'new_count': 0, 'total_fetched': 0, 'error': '사업자번호 미설정'}

    now = timezone.localtime()
    start_date = (now - timedelta(days=days)).strftime('%Y%m%d')
    end_date = now.strftime('%Y%m%d')

    try:
        # 팝빌 계좌 거래내역 조회
        result = service.search(
            config['corp_num'],
            config['bank_code'],
            config['account_number'],
            SDate=start_date,
            EDate=end_date,
            TradeType=["I"],  # I=입금만
            Page=1,
            PerPage=100,
            Order="D",  # 최신순
        )

        items = getattr(result, 'list', []) or []
        new_count = 0

        for item in items:
            tid = getattr(item, 'tid', '') or f"{getattr(item, 'trdate', '')}_{getattr(item, 'trserial', '')}"
            if Deposit.objects.filter(transaction_id=tid).exists():
                continue

            try:
                tr_date_str = getattr(item, 'trdate', '')
                tr_time_str = getattr(item, 'trtime', '000000')
                if tr_date_str:
                    dt = datetime.strptime(f"{tr_date_str}{tr_time_str}", '%Y%m%d%H%M%S')
                    tr_datetime = timezone.make_aware(dt)
                else:
                    tr_datetime = now

                Deposit.objects.create(
                    transaction_date=tr_datetime,
                    depositor_name=getattr(item, 'remark1', '') or getattr(item, 'name', ''),
                    amount=Decimal(str(getattr(item, 'deposit', 0))),
                    balance=Decimal(str(getattr(item, 'balance', 0))) if getattr(item, 'balance', None) else None,
                    memo=getattr(item, 'remark2', '') or '',
                    transaction_id=tid,
                )
                new_count += 1
            except Exception as e:
                logger.warning(f"입금 내역 저장 실패: {e} - item: {vars(item) if hasattr(item, '__dict__') else item}")

        return {'new_count': new_count, 'total_fetched': len(items), 'error': None}

    except Exception as e:
        error_msg = str(e)
        logger.error(f"팝빌 계좌조회 실패: {error_msg}")
        return {'new_count': 0, 'total_fetched': 0, 'error': error_msg}


# ─── 뱅크다(Bankda) ───

def _parse_bankda_datetime(bkdate, bktime):
    """YYYYMMDD + HHMMSS → aware datetime"""
    bkdate = (bkdate or '').strip()
    bktime = (bktime or '000000').strip().zfill(6)
    if not bkdate or len(bkdate) != 8:
        return timezone.localtime()
    try:
        dt = datetime.strptime(f'{bkdate}{bktime}', '%Y%m%d%H%M%S')
    except ValueError:
        return timezone.localtime()
    return timezone.make_aware(dt)


def sync_bankda_deposits():
    """뱅크다 호출 → 새 입금 Deposit 저장 → 자동매칭.

    증분 조회: 마지막으로 저장한 뱅크다 거래 bcode 다음부터.
    첫 호출 시: 오늘부터 일주일 범위.
    """
    from .bankda_client import BankdaClient, BankdaError
    from .models import Deposit

    client = BankdaClient()
    last = (
        Deposit.objects
        .filter(source=Deposit.Source.BANKDA)
        .exclude(bcode='')
        .order_by('-bcode')
        .only('bcode')
        .first()
    )
    last_bcode = last.bcode if last else None

    fetch_kwargs = {'last_bcode': last_bcode}
    if not last_bcode:
        today = timezone.localtime()
        fetch_kwargs['dateto'] = today.strftime('%Y%m%d')
        fetch_kwargs['datefrom'] = (today - timedelta(days=7)).strftime('%Y%m%d')

    try:
        payload = client.fetch_transactions(**fetch_kwargs)
    except BankdaError as exc:
        logger.error('bankda 호출 실패: %s', exc)
        return {'new': 0, 'matched': 0, 'error': str(exc)}

    response = payload.get('response') or {}
    bank_list = response.get('bank') or []

    new_count = 0
    for item in bank_list:
        bcode = str(item.get('bcode') or '').strip()
        if not bcode:
            continue
        try:
            input_amount = int(item.get('bkinput') or 0)
        except (TypeError, ValueError):
            input_amount = 0
        if input_amount <= 0:
            continue
        if Deposit.objects.filter(
            source=Deposit.Source.BANKDA, bcode=bcode
        ).exists():
            continue

        try:
            amount = Decimal(str(input_amount))
            balance_raw = item.get('bkjango')
            balance = Decimal(str(balance_raw)) if balance_raw else None
        except (InvalidOperation, TypeError):
            logger.warning('bankda 금액 파싱 실패 bcode=%s', bcode)
            continue

        try:
            with transaction.atomic():
                Deposit.objects.create(
                    source=Deposit.Source.BANKDA,
                    bcode=bcode,
                    raw_payload=item,
                    transaction_date=_parse_bankda_datetime(
                        item.get('bkdate'), item.get('bktime')
                    ),
                    depositor_name=(item.get('bkcontent') or '').strip()[:100],
                    amount=amount,
                    balance=balance,
                    memo=(item.get('bkjukyo') or '').strip()[:200],
                    transaction_id=f'bankda_{bcode}',
                )
        except Exception as exc:
            logger.warning('bankda Deposit 저장 실패 bcode=%s: %s', bcode, exc)
            continue
        new_count += 1

    matched = auto_match_deposits()
    return {'new': new_count, 'matched': matched, 'error': None}


def auto_match_deposits():
    """미매칭 입금 내역을 주문과 자동 매칭.

    매칭 로직 (2026-05-26 운영자 결정):
    1순위: 금액 일치
    2순위: 입금 시각 - 주문 시각 차이 최소
      (운영자 인용: 주문자명=카톡 ID, 금액 매칭이 가장 정확)

    매칭 후 Order.status는 변경 안 함. 운영자가 컨트롤 패널에서
    확인 후 결제 버튼 직접 클릭 (외상 거래도 같은 흐름).

    Returns:
        int: 매칭된 건수
    """
    from .models import Deposit
    from orders.models import Order, Status

    unmatched = Deposit.objects.filter(
        match_status=Deposit.MatchStatus.UNMATCHED
    ).exclude(amount=0)
    active_orders = Order.objects.filter(status=Status.NEW).exclude(
        deposits__match_status__in=[
            Deposit.MatchStatus.AUTO_MATCHED,
            Deposit.MatchStatus.MANUAL_MATCHED,
        ]
    )

    matched_count = 0
    for deposit in unmatched:
        amount_matches = list(active_orders.filter(total_order_amount=deposit.amount))
        if not amount_matches:
            continue

        if len(amount_matches) == 1:
            chosen = amount_matches[0]
        else:
            chosen = min(
                amount_matches,
                key=lambda o: abs(
                    (deposit.transaction_date - o.payment_date).total_seconds()
                ),
            )

        deposit.matched_order = chosen
        deposit.match_status = Deposit.MatchStatus.AUTO_MATCHED
        deposit.save(update_fields=['matched_order', 'match_status'])
        matched_count += 1

    return matched_count


# ─── 현금영수증 ───

def issue_cash_receipt(cash_receipt_obj):
    """현금영수증 발급 요청

    Args:
        cash_receipt_obj: CashReceipt 모델 인스턴스

    Returns:
        dict: {'success': bool, 'message': str}
    """
    service = _get_cashreceipt_service()
    if not service:
        return {'success': False, 'message': 'popbill 패키지 미설치'}

    config = get_popbill_config()
    if not config['corp_num']:
        return {'success': False, 'message': '사업자번호 미설정'}

    # 식별번호에서 하이픈 제거
    identity_num = cash_receipt_obj.identity_number.replace('-', '')

    # 거래 유형 매핑
    if cash_receipt_obj.trade_type == 'INCOME_DEDUCTION':
        trade_usage = '소득공제용'
    else:
        trade_usage = '지출증빙용'

    # 식별 유형 매핑
    identity_type_map = {
        'BIZ_NO': '사업자등록번호',
        'PHONE': '휴대폰',
        'CARD': '카드',
    }
    id_type = identity_type_map.get(cash_receipt_obj.identity_type, '사업자등록번호')

    try:
        result = service.registIssue(
            config['corp_num'],
            "",  # 문서번호 (자동생성)
            trade_usage,
            int(cash_receipt_obj.amount),  # 거래금액 (공급가 + 세액)
            0,  # 공급가 (0이면 자동계산)
            0,  # 세액 (0이면 자동계산)
            0,  # 봉사료
            id_type,
            identity_num,
            "",  # 고객명
            "",  # 고객 연락처
            "",  # 고객 이메일
            "",  # 가맹점 사업자번호
        )

        cash_receipt_obj.issue_status = 'ISSUED'
        cash_receipt_obj.popbill_receipt_id = getattr(result, 'receiptID', '') or str(result) if result else ''
        cash_receipt_obj.issued_at = timezone.now()
        cash_receipt_obj.error_message = ''
        cash_receipt_obj.save()

        return {'success': True, 'message': '현금영수증이 발급되었습니다.'}

    except Exception as e:
        error_msg = str(e)
        logger.error(f"현금영수증 발급 실패: {error_msg}")
        cash_receipt_obj.issue_status = 'FAILED'
        cash_receipt_obj.error_message = error_msg
        cash_receipt_obj.save()
        return {'success': False, 'message': error_msg}
