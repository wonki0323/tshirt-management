from django.db import models
from django.core.validators import MinValueValidator
from orders.models import Order


class Deposit(models.Model):
    """입금 내역. 출처는 뱅크다(현행) / 수동 / 팝빌(잔재)."""

    class MatchStatus(models.TextChoices):
        UNMATCHED = 'UNMATCHED', '미매칭'
        AUTO_MATCHED = 'AUTO_MATCHED', '자동매칭'
        MANUAL_MATCHED = 'MANUAL_MATCHED', '수동매칭'
        IGNORED = 'IGNORED', '무시'

    class Source(models.TextChoices):
        BANKDA = 'BANKDA', '뱅크다'
        MANUAL = 'MANUAL', '수동'
        POPBILL = 'POPBILL', '팝빌'

    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.BANKDA,
        verbose_name="출처",
    )
    bcode = models.CharField(
        max_length=50, blank=True, default='', db_index=True,
        verbose_name="뱅크다 bcode",
        help_text="뱅크다 데이터 일련번호 (증분/중복 방지)",
    )
    raw_payload = models.JSONField(default=dict, blank=True, verbose_name="원본 응답")

    # 입금 내역
    transaction_date = models.DateTimeField(verbose_name="거래일시")
    depositor_name = models.CharField(max_length=100, verbose_name="입금자명")
    amount = models.DecimalField(
        max_digits=12, decimal_places=0,
        validators=[MinValueValidator(0)],
        verbose_name="입금액"
    )
    balance = models.DecimalField(
        max_digits=14, decimal_places=0,
        null=True, blank=True,
        verbose_name="거래 후 잔액"
    )
    memo = models.CharField(max_length=200, blank=True, default='', verbose_name="적요")
    transaction_id = models.CharField(
        max_length=100, unique=True,
        verbose_name="거래 고유번호",
        help_text="팝빌 거래내역의 고유 식별자 (중복 방지)"
    )

    # 매칭 정보
    matched_order = models.ForeignKey(
        Order, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='deposits',
        verbose_name="매칭된 주문"
    )
    match_status = models.CharField(
        max_length=20,
        choices=MatchStatus.choices,
        default=MatchStatus.UNMATCHED,
        verbose_name="매칭 상태"
    )
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name="확인 일시")
    confirmed_by = models.CharField(max_length=50, blank=True, default='', verbose_name="확인자")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="수신일시")

    class Meta:
        verbose_name = "입금 내역"
        verbose_name_plural = "입금 내역"
        ordering = ['-transaction_date']
        constraints = [
            models.UniqueConstraint(
                fields=['source', 'bcode'],
                condition=models.Q(bcode__gt=''),
                name='unique_source_bcode',
            ),
        ]

    def __str__(self):
        return f"{self.transaction_date:%Y-%m-%d %H:%M} {self.depositor_name} {self.amount:,.0f}원"


class CashReceipt(models.Model):
    """현금영수증 발급 이력"""

    class IdentityType(models.TextChoices):
        BIZ_NO = 'BIZ_NO', '사업자번호'
        PHONE = 'PHONE', '휴대폰번호'
        CARD = 'CARD', '카드번호'

    class TradeType(models.TextChoices):
        INCOME_DEDUCTION = 'INCOME_DEDUCTION', '소득공제용'
        EXPENDITURE_PROOF = 'EXPENDITURE_PROOF', '지출증빙용'

    class IssueStatus(models.TextChoices):
        PENDING = 'PENDING', '발급 대기'
        ISSUED = 'ISSUED', '발급 완료'
        FAILED = 'FAILED', '발급 실패'
        CANCELED = 'CANCELED', '발급 취소'

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE,
        related_name='cash_receipts',
        verbose_name="주문"
    )
    identity_type = models.CharField(
        max_length=10,
        choices=IdentityType.choices,
        default=IdentityType.BIZ_NO,
        verbose_name="식별 유형"
    )
    identity_number = models.CharField(
        max_length=30,
        verbose_name="식별번호",
        help_text="사업자번호, 휴대폰번호, 또는 카드번호"
    )
    trade_type = models.CharField(
        max_length=20,
        choices=TradeType.choices,
        default=TradeType.EXPENDITURE_PROOF,
        verbose_name="거래 유형"
    )
    amount = models.DecimalField(
        max_digits=12, decimal_places=0,
        validators=[MinValueValidator(0)],
        verbose_name="발급 금액"
    )
    issue_status = models.CharField(
        max_length=10,
        choices=IssueStatus.choices,
        default=IssueStatus.PENDING,
        verbose_name="발급 상태"
    )
    # 팝빌 응답 데이터
    popbill_receipt_id = models.CharField(
        max_length=100, blank=True, default='',
        verbose_name="팝빌 접수번호"
    )
    popbill_nts_confirm_num = models.CharField(
        max_length=100, blank=True, default='',
        verbose_name="국세청 승인번호"
    )
    error_message = models.TextField(blank=True, default='', verbose_name="오류 메시지")

    issued_at = models.DateTimeField(null=True, blank=True, verbose_name="발급일시")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")

    class Meta:
        verbose_name = "현금영수증"
        verbose_name_plural = "현금영수증"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order.customer_name} {self.amount:,.0f}원 ({self.get_issue_status_display()})"
