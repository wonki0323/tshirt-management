from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from products.models import ProductOption


class Status(models.TextChoices):
    """주문 처리 워크플로우 상태"""
    NEW = 'NEW', '신규 주문'
    CONSULTING = 'CONSULTING', '상담/시안 제작 중'
    PRODUCING = 'PRODUCING', '제작 중'
    PRODUCED = 'PRODUCED', '제작 완료 (발송 대기)'
    COMPLETED = 'COMPLETED', '완료 (정산 포함)'
    CANCELED = 'CANCELED', '주문 취소'


class Order(models.Model):
    """주문 기본 정보"""
    smartstore_order_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="스마트스토어 주문 ID",
        help_text="스마트스토어에서 제공하는 고유 주문 ID"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        verbose_name="주문 상태"
    )
    payment_date = models.DateTimeField(
        default=timezone.now,
        verbose_name="결제일시"
    )
    customer_name = models.CharField(
        max_length=100,
        verbose_name="고객명"
    )
    customer_phone = models.CharField(
        max_length=20,
        verbose_name="연락처"
    )
    shipping_address = models.TextField(
        verbose_name="배송 주소"
    )
    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=3500,
        validators=[MinValueValidator(0)],
        verbose_name="택배비",
        help_text="기본 3,500원 (제주/도서산간 변경 가능)"
    )
    total_order_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="총 결제 금액 (택배비 포함)"
    )
    confirmed_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="고객 컨펌 완료일시"
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="발송 마감 예정일",
        help_text="컨펌일로부터 +3 영업일"
    )
    google_drive_folder_url = models.URLField(
        null=True,
        blank=True,
        verbose_name="구글 드라이브 폴더 링크",
        help_text="시안/원본 통합 관리용"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")

    class Meta:
        verbose_name = "주문"
        verbose_name_plural = "주문"
        ordering = ['-payment_date']

    def __str__(self):
        return f"{self.smartstore_order_id} - {self.customer_name}"

    @property
    def total_cost(self):
        """주문의 총 원가 계산 (제품 원가 + 택배비)"""
        items_cost = sum(item.total_cost for item in self.items.all())
        return items_cost + self.shipping_cost

    @property
    def profit(self):
        """주문의 순이익 계산 (총 결제금액 - 총 원가)"""
        return self.total_order_amount - self.total_cost
    
    @property
    def is_general_order(self):
        """주문에 'GOODS' 카테고리 상품이 포함되어 있는지 확인합니다. 
           'GOODS'가 없으면 True (일반 주문), 있으면 False를 반환합니다."""
        has_goods = self.items.filter(product_option__product__category='GOODS').exists()
        return not has_goods


class OrderItem(models.Model):
    """주문 상세 항목"""
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="주문"
    )
    product_option = models.ForeignKey(
        ProductOption,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="제품 옵션",
        help_text="관리자가 매핑한 내부 제품 옵션"
    )
    smartstore_product_name = models.CharField(
        max_length=200,
        verbose_name="스마트스토어 제품명",
        help_text="원본 데이터 보존용"
    )
    smartstore_option_text = models.TextField(
        verbose_name="스마트스토어 옵션 텍스트",
        help_text="스마트스토어에서 넘어온 원본 옵션 텍스트"
    )
    manual_text = models.TextField(
        blank=True,
        default='',
        verbose_name="수동 입력 항목 (메모)",
        help_text="제품 옵션을 선택하지 않고 수동으로 입력한 항목 또는 메모"
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="수량"
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="개당 판매 가격"
    )
    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="개당 원가",
        help_text="주문 시점의 ProductOption.base_cost를 복사하여 저장"
    )
    design_image_url = models.URLField(
        null=True,
        blank=True,
        verbose_name="시안/원본 이미지 링크",
        help_text="해당 항목의 시안/원본 이미지 개별 링크"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")

    class Meta:
        verbose_name = "주문 항목"
        verbose_name_plural = "주문 항목"
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.order.smartstore_order_id} - {self.smartstore_product_name}"

    @property
    def total_price(self):
        """항목의 총 판매 가격"""
        return self.unit_price * self.quantity

    @property
    def total_cost(self):
        """항목의 총 원가"""
        return self.unit_cost * self.quantity

    @property
    def profit(self):
        """항목의 순이익"""
        return self.total_price - self.total_cost