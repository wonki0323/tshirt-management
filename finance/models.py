from django.db import models
from django.core.validators import MinValueValidator


class Expense(models.Model):
    """지출 내역"""
    EXPENSE_CATEGORIES = [
        ('SHIPPING', '배송비'),
        ('ADVERTISING', '광고비'),
        ('MATERIALS', '재료비 추가 구매'),
        ('EQUIPMENT', '장비 구매/수리'),
        ('UTILITIES', '공과금'),
        ('RENT', '임대료'),
        ('OTHER', '기타'),
    ]

    date = models.DateField(
        verbose_name="지출 일자"
    )
    category = models.CharField(
        max_length=20,
        choices=EXPENSE_CATEGORIES,
        verbose_name="지출 항목"
    )
    description = models.TextField(
        blank=True,
        verbose_name="상세 설명"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="지출 금액"
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="수량"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")

    class Meta:
        verbose_name = "지출"
        verbose_name_plural = "지출"
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.date} - {self.get_category_display()} - {self.amount:,}원"

    @property
    def total_amount(self):
        """총 지출 금액 (금액 × 수량)"""
        return self.amount * self.quantity


class Purchase(models.Model):
    """매입 내역 (재료비)"""
    PURCHASE_CATEGORIES = [
        ('TSHIRT', '티셔츠'),
        ('HOODIE', '후드티'),
        ('INK', '잉크'),
        ('PRINTER_SUPPLIES', '프린터 부자재'),
        ('OTHER', '기타'),
    ]

    date = models.DateField(
        verbose_name="매입 일자"
    )
    category = models.CharField(
        max_length=20,
        choices=PURCHASE_CATEGORIES,
        verbose_name="매입 항목"
    )
    description = models.TextField(
        blank=True,
        verbose_name="상세 설명"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="매입 금액"
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="수량"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")

    class Meta:
        verbose_name = "매입"
        verbose_name_plural = "매입"
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.date} - {self.get_category_display()} - {self.amount:,}원"

    @property
    def total_amount(self):
        """총 매입 금액 (금액 × 수량)"""
        return self.amount * self.quantity