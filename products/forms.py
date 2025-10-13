from django import forms
from django.forms import inlineformset_factory
from .models import Product, ProductOption, CategoryChoices


class ProductForm(forms.ModelForm):
    """제품 폼"""
    
    class Meta:
        model = Product
        fields = ['name', 'category', 'is_active']
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


class ProductOptionForm(forms.ModelForm):
    """제품 옵션 폼"""
    
    class Meta:
        model = ProductOption
        fields = ['option_detail', 'base_cost', 'is_active']
        widgets = {
            'option_detail': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '예: 화이트 / L 사이즈'
            }),
            'base_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '100',
                'min': '0'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }


# 인라인 폼셋 생성
ProductOptionFormSet = inlineformset_factory(
    Product,
    ProductOption,
    form=ProductOptionForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False
)
