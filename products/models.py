from django.db import models
from django.core.validators import MinValueValidator


class CategoryChoices(models.TextChoices):
    GOODS = 'GOODS', '굿즈 (시안 필요)'
    GENERAL = 'GENERAL', '일반 (시안 불필요)'


class Product(models.Model):
    """기본 제품 모델"""
    name = models.CharField(
        max_length=200,
        verbose_name="제품명",
        help_text="예: 라운드 반팔 티셔츠"
    )
    category = models.CharField(
        max_length=10,
        choices=CategoryChoices.choices,
        default=CategoryChoices.GOODS,
        verbose_name="카테고리",
        help_text="굿즈는 시안이 필요하고, 일반은 시안이 불필요합니다"
    )
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=0,  # 소수점 제거 (정수만)
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="기본 판매가",
        help_text="제품의 기본 판매 가격 (옵션별로 다를 수 있음)"
    )
    base_cost = models.DecimalField(
        max_digits=10,
        decimal_places=0,  # 소수점 제거 (정수만)
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="기본 원가",
        help_text="옵션이 없을 때 사용되는 기본 제품 원가"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="활성화",
        help_text="제품이 판매 가능한 상태인지 여부"
    )
    is_physical = models.BooleanField(
        default=True,
        verbose_name="실물",
        help_text="실물 제품인지 여부 (캘린더에서 개수 집계 시 사용)"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")

    class Meta:
        verbose_name = "제품"
        verbose_name_plural = "제품"
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductOption(models.Model):
    """제품 세부 옵션 및 원가 관리"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='options',
        verbose_name="제품"
    )
    option_detail = models.CharField(
        max_length=200,
        verbose_name="옵션 상세",
        help_text="예: 화이트 / L 사이즈"
    )
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=0,  # 소수점 제거 (정수만)
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="판매가",
        help_text="이 옵션의 판매 가격"
    )
    base_cost = models.DecimalField(
        max_digits=10,
        decimal_places=0,  # 소수점 제거 (정수만)
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="제품 원가 (부가세 포함)",
        help_text="이 옵션의 원가 (부가세 포함)"
    )
    stock_quantity = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="재고 수량",
        help_text="재고 수량 (NULL이면 무제한)"
    )
    track_inventory = models.BooleanField(
        default=True,
        verbose_name="재고 추적",
        help_text="재고를 추적할지 여부 (프린터 잉크 등은 체크 해제)"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="활성화",
        help_text="옵션이 판매 가능한 상태인지 여부"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")

    class Meta:
        verbose_name = "제품 옵션"
        verbose_name_plural = "제품 옵션"
        ordering = ['product', 'option_detail']
        unique_together = ['product', 'option_detail']

    def __str__(self):
        return f"{self.product.name} - {self.option_detail}"
    
    @property
    def is_goods(self):
        """굿즈 카테고리인지 확인"""
        return self.product.category == CategoryChoices.GOODS
    
    @property
    def is_general(self):
        """일반 카테고리인지 확인"""
        return self.product.category == CategoryChoices.GENERAL
    
    @property
    def stock_status(self):
        """재고 상태 반환"""
        if not self.track_inventory:
            return "무제한"
        if self.stock_quantity is None:
            return "무제한"
        if self.stock_quantity <= 0:
            return "품절"
        if self.stock_quantity <= 10:
            return "부족"
        return "정상"
    
    def decrease_stock(self, quantity):
        """재고 차감"""
        if not self.track_inventory:
            return True
        if self.stock_quantity is None:
            return True
        if self.stock_quantity >= quantity:
            self.stock_quantity -= quantity
            self.save()
            return True
        return False
    
    def increase_stock(self, quantity):
        """재고 증가"""
        if not self.track_inventory:
            return
        if self.stock_quantity is None:
            self.stock_quantity = quantity
        else:
            self.stock_quantity += quantity
        self.save()