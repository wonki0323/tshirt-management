from django import forms
from django.forms import inlineformset_factory
from .models import Product, ProductOption, CategoryChoices


class ProductForm(forms.ModelForm):
    """제품 폼"""
    
    # 기본 판매가 필드를 CharField로 재정의 (콤마 입력 허용)
    base_price = forms.CharField(
        initial='0',
        required=False,
        label="기본 판매가 (원)",
        widget=forms.TextInput(attrs={
            'class': 'form-control price-input',
            'placeholder': '기본 판매가 (원)',
            'inputmode': 'numeric',
            'pattern': '[0-9,]*'
        }),
        help_text="옵션이 없을 때 사용되는 기본 판매 가격"
    )
    
    class Meta:
        model = Product
        fields = ['name', 'category', 'base_price', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '제품명을 입력하세요'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def clean_base_price(self):
        """기본 판매가에서 콤마 제거하고 정수로 변환"""
        value = self.cleaned_data.get('base_price', '0')
        if not value or value == '':
            return 0
        # 문자열인 경우 콤마 제거
        if isinstance(value, str):
            value = value.replace(',', '').strip()
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0


class ProductOptionForm(forms.ModelForm):
    """제품 옵션 폼"""
    
    # 판매가 필드를 CharField로 재정의 (콤마 입력 허용)
    base_price = forms.CharField(
        initial='0',
        required=False,
        label="판매가 (원)",
        widget=forms.TextInput(attrs={
            'class': 'form-control price-input',
            'placeholder': '판매가 (원)',
            'inputmode': 'numeric',
            'pattern': '[0-9,]*'
        })
    )
    
    class Meta:
        model = ProductOption
        fields = ['option_detail', 'base_price', 'stock_quantity', 'track_inventory', 'is_active']
        widgets = {
            'option_detail': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '예: 화이트 / L 사이즈'
            }),
            'stock_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '재고 수량 (비워두면 무제한)',
                'min': '0'
            }),
            'track_inventory': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def clean_base_price(self):
        """판매가에서 콤마 제거하고 정수로 변환"""
        value = self.cleaned_data.get('base_price', '0')
        if not value or value == '':
            return 0
        if isinstance(value, str):
            value = value.replace(',', '').strip()
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0


# 인라인 폼셋 생성
ProductOptionFormSet = inlineformset_factory(
    Product,
    ProductOption,
    form=ProductOptionForm,
    extra=3,  # 기본적으로 3개의 빈 폼 표시
    can_delete=True,
    min_num=0,
    validate_min=False
)
