from django.urls import path
from . import views

urlpatterns = [
    path('', views.OrderListView.as_view(), name='order_list'),
    path('<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('<int:pk>/update/', views.order_update, name='order_update'),
    path('<int:pk>/cancel/', views.cancel_order, name='cancel_order'),
    path('<int:pk>/completion/', views.order_completion, name='order_completion'),
    path('<int:pk>/completion-info/', views.get_completion_info, name='get_completion_info'),
    path('change-status/', views.change_order_status, name='change_order_status'),
    path('export-excel/', views.export_shipping_excel, name='export_shipping_excel'),
    path('upload-design/', views.upload_design_and_confirm, name='upload_design_and_confirm'),
    path('manual-create/', views.manual_order_create, name='manual_order_create'),
    path('check-customer/', views.check_customer_exists, name='check_customer_exists'),
    path('debug-upload/', views.debug_upload, name='debug_upload'),
    path('settlement/', views.settlement_list, name='settlement_list'),
    path('archived/', views.archived_list, name='archived_list'),
    path('<int:pk>/archive/', views.archive_order, name='archive_order'),
]
