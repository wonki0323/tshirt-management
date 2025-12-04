"""
주문 관련 폼
"""
import re
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from .models import Order, OrderItem, PrintMethod
from products.models import ProductOption
from utils.customer_utils import generate_customer_id


class ManualOrderForm(forms.Form):
    """수동 주문 등록 폼"""
    
    # 고객 정보 (이름만 필수)
    customer_name = forms.CharField(
        max_length=100,
        label="고객명",
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '고객명을 입력하세요 (필수)',
            'id': 'id_customer_name'
        })
    )
    
    customer_phone = forms.CharField(
        max_length=20,
        label="연락처",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '010-1234-5678 (선택)',
            'id': 'id_customer_phone'
        })
    )
    
    shipping_address = forms.CharField(
        label="배송 주소",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': '주소 검색 버튼을 클릭하세요 (선택)',
            'id': 'id_shipping_address',
            'readonly': 'readonly'
        })
    )
    
    customer_memo = forms.CharField(
        label="고객 메모",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': '고객에 대한 특이사항이나 주문 관련 메모 (선택)',
            'id': 'id_customer_memo'
        })
    )
    
    print_method = forms.ChoiceField(
        choices=[('', '선택안함')] + list(PrintMethod.choices),
        label="인쇄 방법",
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_print_method'
        })
    )
    
    # 주문 정보
    shipping_cost = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        initial=3500,
        label="택배비",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '3500',
            'id': 'id_shipping_cost',
            'value': '3500'
        }),
        help_text="기본 3,500원 (제주/도서산간 변경 가능)"
    )
    
    manual_total_input = forms.BooleanField(
        required=False,
        initial=False,
        label="총 결제금액 수동 입력",
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'id_manual_total_input'
        }),
        help_text="체크하면 자동 합산이 비활성화됩니다"
    )
    
    total_order_amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        label="총 결제 금액 (택배비 포함)",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0',
            'id': 'id_total_order_amount',
            'readonly': 'readonly'
        })
    )
    
    due_date = forms.DateField(
        required=False,
        label="발송 마감일",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'id': 'id_due_date'
        }),
        help_text="발송 마감 예정일을 선택하세요"
    )
    
    # 제품 옵션 선택 (수량 입력 방식으로 변경되어 사용하지 않음, 하지만 템플릿 에러 방지를 위해 유지)
    # product_options = forms.ModelMultipleChoiceField(
    #     queryset=ProductOption.objects.filter(is_active=True),
    #     label="제품 옵션 선택",
    #     widget=forms.CheckboxSelectMultiple(attrs={
    #         'class': 'form-check-input'
    #     }),
    #     required=False,
    #     help_text="등록된 제품 옵션 중에서 선택하세요"
    # )
    
    # 수동 입력 항목 (메모)
    manual_items = forms.CharField(
        label="수동 입력 항목 / 메모 (선택사항)",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': '제품 옵션을 선택하지 않고 직접 입력하거나 메모를 작성하세요',
            'id': 'id_manual_items'
        }),
        required=False,
        help_text="제품 옵션 대신 텍스트로 주문 내용을 입력하거나 메모로 활용할 수 있습니다"
    )
    
    def clean_customer_phone(self):
        """연락처 유효성 검사 (선택사항)"""
        phone = self.cleaned_data.get('customer_phone')
        if phone and phone.strip():
            # 숫자만 추출
            phone_digits = re.sub(r'[^\d]', '', phone)
            if len(phone_digits) < 10:
                raise ValidationError('올바른 연락처를 입력해주세요.')
        return phone if phone else ''
    
    def clean(self):
        """전체 폼 유효성 검사 (이름만 필수)"""
        import logging
        logger = logging.getLogger(__name__)
        
        cleaned_data = super().clean()
        customer_name = cleaned_data.get('customer_name')
        manual_items = cleaned_data.get('manual_items')
        total_order_amount = cleaned_data.get('total_order_amount')
        
        logger.info("=== 폼 유효성 검사 시작 ===")
        logger.info(f"customer_name: {customer_name}")
        logger.info(f"manual_items: {manual_items}")
        logger.info(f"total_order_amount: {total_order_amount}")
        
        # 고객명은 필수
        if not customer_name or not customer_name.strip():
            raise ValidationError('고객명은 필수 입력 항목입니다.')
        
        # POST 데이터에서 수량이 입력된 제품 옵션 확인
        has_product_options = False
        if hasattr(self, 'data') and self.data:
            logger.info(f"POST 데이터 키: {list(self.data.keys())}")
            for key in self.data.keys():
                if key.startswith('product_option_'):
                    try:
                        value = self.data.get(key, '')
                        logger.info(f"{key}: {value}")
                        if value and value.strip():
                            quantity = int(value)
                            if quantity > 0:
                                has_product_options = True
                                logger.info(f"수량 입력 발견: {key} = {quantity}")
                                break
                    except (ValueError, TypeError) as e:
                        logger.warning(f"{key} 변환 실패: {e}")
                        continue
        
        logger.info(f"has_product_options: {has_product_options}")
        
        # 제품 옵션이나 수동 입력 중 하나는 있어야 함
        if not has_product_options and not manual_items:
            logger.warning("제품 옵션도 없고 수동 입력도 없음 - 주문 내용이 비어있음")
            # 이름만 있어도 진행 가능하도록 경고만 로깅
            logger.info("이름만 입력된 상태로 주문 생성 허용")
        
        return cleaned_data
    
    def save(self):
        """폼 데이터를 저장하고 Order 객체를 반환"""
        import re
        from django.utils import timezone
        
        # 고객 ID 생성
        customer_name = self.cleaned_data['customer_name']
        customer_phone = self.cleaned_data.get('customer_phone', '') or ''
        final_customer_name = generate_customer_id(customer_name, customer_phone) if customer_phone else customer_name
        
        # 주문 ID 생성 (수동 등록용) - 중복 방지
        base_id = f"M{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        manual_order_id = base_id
        counter = 1
        while Order.objects.filter(smartstore_order_id=manual_order_id).exists():
            manual_order_id = f"{base_id}_{counter}"
            counter += 1
        
        # 주문 생성
        order = Order.objects.create(
            smartstore_order_id=manual_order_id,
            customer_name=final_customer_name,
            customer_phone=customer_phone or '',
            shipping_address=self.cleaned_data.get('shipping_address', '') or '',
            customer_memo=self.cleaned_data.get('customer_memo', '') or '',
            print_method=self.cleaned_data.get('print_method') or None,
            shipping_cost=self.cleaned_data.get('shipping_cost', Decimal('3500')),
            total_order_amount=self.cleaned_data.get('total_order_amount', Decimal('0')),
            payment_date=timezone.now(),  # 자동으로 현재 시각 설정
            due_date=self.cleaned_data.get('due_date')
        )
        
        # 제품 옵션 선택 처리 (수량 포함)
        from products.models import ProductOption
        
        for key, value in self.data.items():
            if key.startswith('product_option_'):
                try:
                    quantity = int(value) if value else 0
                    if quantity > 0:
                        # 옵션 ID 추출
                        option_id = int(key.replace('product_option_', ''))
                        product_option = ProductOption.objects.get(id=option_id)
                        
                        # 단가 = 제품 기본가 + 옵션가
                        unit_price = product_option.product.base_price + product_option.base_price
                        
                        OrderItem.objects.create(
                            order=order,
                            product_option=product_option,
                            smartstore_product_name=product_option.product.name,
                            smartstore_option_text=product_option.option_detail,
                            quantity=quantity,
                            unit_price=unit_price,
                            unit_cost=0  # 수동 등록은 원가 0
                        )
                except (ValueError, TypeError, ProductOption.DoesNotExist) as e:
                    # 잘못된 값이나 존재하지 않는 옵션은 건너뜀
                    continue
        
        # 수동 입력 항목 처리 (메모로 저장)
        manual_items = self.cleaned_data.get('manual_items', '')
        
        # 제품 옵션 개수 확인
        has_product_items = OrderItem.objects.filter(order=order).exists()
        
        if manual_items and not has_product_items:
            # 제품 옵션이 없고 수동 입력만 있는 경우, 하나의 OrderItem으로 저장
            OrderItem.objects.create(
                order=order,
                smartstore_product_name="수동 입력 주문",
                smartstore_option_text="",
                manual_text=manual_items,
                quantity=1,
                unit_price=self.cleaned_data['total_order_amount'] - self.cleaned_data.get('shipping_cost', Decimal('3500')),
                unit_cost=0  # 수동 등록시 원가는 0으로 설정
            )
        
        return order


class OrderUpdateForm(forms.ModelForm):
    """주문 정보 수정 폼 (모든 단계에서 사용 가능)"""
    
    class Meta:
        model = Order
        fields = [
            'customer_name', 'customer_phone', 'shipping_address',
            'customer_memo', 'print_method', 'tracking_number',
            'shipping_cost', 'total_order_amount', 'due_date', 'status'
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '고객명'
            }),
            'customer_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '010-1234-5678'
            }),
            'shipping_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '배송 주소'
            }),
            'customer_memo': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '고객 메모'
            }),
            'print_method': forms.Select(attrs={
                'class': 'form-control'
            }),
            'tracking_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '송장번호'
            }),
            'shipping_cost': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
            'total_order_amount': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
            'payment_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 모든 필드를 선택사항으로 (고객명 제외)
        for field_name in self.fields:
            if field_name != 'customer_name':
                self.fields[field_name].required = False
