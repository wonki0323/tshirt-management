"""
재무 관련 폼
"""
from django import forms
from django.utils import timezone
from .models import Purchase, Expense


class PurchaseForm(forms.ModelForm):
    """매입 등록 폼"""
    
    date = forms.DateField(
        initial=timezone.now,
        label="매입 일자",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )
    
    category = forms.ChoiceField(
        choices=Purchase.PURCHASE_CATEGORIES,
        label="매입 항목",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    description = forms.CharField(
        label="상세 설명",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': '예: 화이트 라운드 티셔츠 L/XL 사이즈'
        })
    )
    
    amount = forms.DecimalField(
        label="단가 (원)",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0',
            'min': '0',
            'step': '0.01'
        })
    )
    
    quantity = forms.IntegerField(
        initial=1,
        label="수량",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1',
            'min': '1'
        })
    )
    
    class Meta:
        model = Purchase
        fields = ['date', 'category', 'description', 'amount', 'quantity']


class ExpenseForm(forms.ModelForm):
    """지출 등록 폼"""
    
    date = forms.DateField(
        initial=timezone.now,
        label="지출 일자",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )
    
    category = forms.ChoiceField(
        choices=Expense.EXPENSE_CATEGORIES,
        label="지출 항목",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    description = forms.CharField(
        label="상세 설명",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': '예: 스마트스토어 광고비 (1월 2주차)'
        })
    )
    
    amount = forms.DecimalField(
        label="금액 (원)",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0',
            'min': '0',
            'step': '0.01'
        })
    )
    
    quantity = forms.IntegerField(
        initial=1,
        label="수량",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1',
            'min': '1'
        })
    )
    
    class Meta:
        model = Expense
        fields = ['date', 'category', 'description', 'amount', 'quantity']

