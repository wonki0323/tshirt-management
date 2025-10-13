"""
주문 관련 폼
"""
import re
from django import forms
from django.core.exceptions import ValidationError
from .models import Order, OrderItem
from products.models import ProductOption
from utils.customer_utils import generate_customer_id


class ManualOrderForm(forms.Form):
    """수동 주문 등록 폼"""
    
    # 고객 정보
    customer_name = forms.CharField(
        max_length=100,
        label="고객명",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '고객명을 입력하세요'
        })
    )
    
    customer_phone = forms.CharField(
        max_length=20,
        label="연락처",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '010-1234-5678'
        })
    )
    
    shipping_address = forms.CharField(
        label="배송 주소",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': '배송 주소를 입력하세요'
        })
    )
    
    # 주문 정보
    total_order_amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        label="총 결제 금액",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0'
        })
    )
    
    payment_date = forms.DateTimeField(
        label="결제일시",
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        })
    )
    
    # 제품 옵션 선택
    product_options = forms.ModelMultipleChoiceField(
        queryset=ProductOption.objects.filter(is_active=True),
        label="제품 옵션 선택",
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        required=False,
        help_text="등록된 제품 옵션 중에서 선택하세요"
    )
    
    # 수동 입력 항목들
    manual_items = forms.CharField(
        label="수동 입력 항목 (선택사항)",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': '제품명, 옵션, 수량, 단가를 한 줄씩 입력하세요\n예: 라운드 반팔 티셔츠, 화이트/L, 2, 15000'
        }),
        required=False,
        help_text="각 항목을 한 줄씩 입력하세요. 형식: 제품명, 옵션, 수량, 단가"
    )
    
    def clean_customer_phone(self):
        """연락처 유효성 검사"""
        phone = self.cleaned_data.get('customer_phone')
        if phone:
            # 숫자만 추출
            phone_digits = re.sub(r'[^\d]', '', phone)
            if len(phone_digits) < 10:
                raise ValidationError('올바른 연락처를 입력해주세요.')
        return phone
    
    def clean_manual_items(self):
        """수동 입력 항목 유효성 검사"""
        manual_items = self.cleaned_data.get('manual_items')
        if not manual_items:
            return manual_items
        
        lines = manual_items.strip().split('\n')
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            parts = [part.strip() for part in line.split(',')]
            if len(parts) != 4:
                raise ValidationError(f'{i}번째 줄의 형식이 올바르지 않습니다. 형식: 제품명, 옵션, 수량, 단가')
            
            try:
                quantity = int(parts[2])
                unit_price = float(parts[3])
                if quantity <= 0 or unit_price < 0:
                    raise ValueError()
            except ValueError:
                raise ValidationError(f'{i}번째 줄의 수량 또는 단가가 올바르지 않습니다.')
        
        return manual_items
    
    def clean(self):
        """전체 폼 유효성 검사"""
        cleaned_data = super().clean()
        product_options = cleaned_data.get('product_options')
        manual_items = cleaned_data.get('manual_items')
        
        # 제품 옵션 선택과 수동 입력 중 하나는 반드시 있어야 함
        if not product_options and not manual_items:
            raise ValidationError('제품 옵션을 선택하거나 수동으로 주문 항목을 입력해주세요.')
        
        return cleaned_data
    
    def save(self):
        """폼 데이터를 저장하고 Order 객체를 반환"""
        import re
        from django.utils import timezone
        
        # 고객 ID 생성
        customer_name = self.cleaned_data['customer_name']
        customer_phone = self.cleaned_data['customer_phone']
        final_customer_name = generate_customer_id(customer_name, customer_phone)
        
        # 주문 ID 생성 (수동 등록용) - 중복 방지
        base_id = f"MANUAL_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        manual_order_id = base_id
        counter = 1
        while Order.objects.filter(smartstore_order_id=manual_order_id).exists():
            manual_order_id = f"{base_id}_{counter}"
            counter += 1
        
        # 주문 생성
        order = Order.objects.create(
            smartstore_order_id=manual_order_id,
            customer_name=final_customer_name,
            customer_phone=customer_phone,
            shipping_address=self.cleaned_data['shipping_address'],
            total_order_amount=self.cleaned_data['total_order_amount'],
            payment_date=self.cleaned_data['payment_date']
        )
        
        # 제품 옵션 선택 처리
        product_options = self.cleaned_data.get('product_options', [])
        for product_option in product_options:
            # 수량과 단가를 기본값으로 설정 (실제로는 사용자가 입력해야 함)
            quantity = 1  # 기본 수량
            unit_price = product_option.base_cost * 2  # 기본 판매가 (원가의 2배)
            
            OrderItem.objects.create(
                order=order,
                product_option=product_option,
                smartstore_product_name=product_option.product.name,
                smartstore_option_text=product_option.option_detail,
                quantity=quantity,
                unit_price=unit_price,
                unit_cost=product_option.base_cost
            )
        
        # 수동 입력 항목들 처리
        manual_items = self.cleaned_data.get('manual_items', '')
        if manual_items:
            lines = manual_items.strip().split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                parts = [part.strip() for part in line.split(',')]
                if len(parts) >= 4:
                    product_name = parts[0]
                    option_text = parts[1]
                    try:
                        quantity = int(parts[2])
                        unit_price = float(parts[3])
                        
                        # OrderItem 생성
                        OrderItem.objects.create(
                            order=order,
                            smartstore_product_name=product_name,
                            smartstore_option_text=option_text,
                            quantity=quantity,
                            unit_price=unit_price,
                            unit_cost=0  # 수동 등록시 원가는 0으로 설정
                        )
                    except (ValueError, IndexError) as e:
                        # 잘못된 형식의 항목은 건너뛰기
                        continue
        
        return order
