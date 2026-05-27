from django.urls import path
from . import views

urlpatterns = [
    # 메인 대시보드
    path('', views.popbill_dashboard, name='popbill_dashboard'),

    # 입금확인
    path('deposits/fetch/', views.fetch_deposits, name='fetch_deposits'),
    path('deposits/<int:pk>/confirm/', views.confirm_deposit, name='confirm_deposit'),
    path('deposits/<int:pk>/match/', views.match_deposit, name='match_deposit'),
    path('deposits/<int:pk>/ignore/', views.ignore_deposit, name='ignore_deposit'),
    path('deposits/matching-orders/', views.get_matching_orders, name='get_matching_orders'),

    # 현금영수증
    path('receipt/<int:order_id>/form/', views.issue_receipt_form, name='issue_receipt_form'),
    path('receipt/<int:order_id>/issue/', views.issue_receipt, name='issue_receipt'),
    path('receipt/history/', views.receipt_history, name='receipt_history'),

    # 컨트롤 패널 팝업
    path('control-panel/', views.control_panel, name='control_panel'),
]
