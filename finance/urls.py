from django.urls import path
from . import views

urlpatterns = [
    # 재무 요약
    path('', views.financial_summary, name='financial_summary'),
    
    # 순이익 요약
    path('net-profit/', views.net_profit_summary, name='net_profit_summary'),
    
    # 지출 관리
    path('expenses/', views.ExpenseListView.as_view(), name='expense_list'),
    path('expenses/create/', views.ExpenseCreateView.as_view(), name='expense_create'),
    path('expenses/<int:pk>/delete/', views.ExpenseDeleteView.as_view(), name='expense_delete'),
    
    # 매입 관리
    path('purchases/', views.PurchaseListView.as_view(), name='purchase_list'),
    path('purchases/create/', views.PurchaseCreateView.as_view(), name='purchase_create'),
    path('purchases/<int:pk>/delete/', views.PurchaseDeleteView.as_view(), name='purchase_delete'),
]
