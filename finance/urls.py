from django.urls import path
from . import views

urlpatterns = [
    path('expenses/', views.ExpenseListView.as_view(), name='expense_list'),
    path('purchases/', views.PurchaseListView.as_view(), name='purchase_list'),
]
