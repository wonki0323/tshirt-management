from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from .models import Expense, Purchase


class ExpenseListView(LoginRequiredMixin, ListView):
    """지출 목록 조회"""
    model = Expense
    template_name = 'finance/expense_list.html'
    context_object_name = 'expenses'
    paginate_by = 20
    ordering = ['-date', '-created_at']


class PurchaseListView(LoginRequiredMixin, ListView):
    """매입 목록 조회"""
    model = Purchase
    template_name = 'finance/purchase_list.html'
    context_object_name = 'purchases'
    paginate_by = 20
    ordering = ['-date', '-created_at']