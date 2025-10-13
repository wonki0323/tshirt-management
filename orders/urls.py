from django.urls import path
from . import views

urlpatterns = [
    path('', views.OrderListView.as_view(), name='order_list'),
    path('<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('<int:pk>/cancel/', views.cancel_order, name='cancel_order'),
    path('change-status/', views.change_order_status, name='change_order_status'),
    path('export-excel/', views.export_shipping_excel, name='export_shipping_excel'),
    path('upload-design/', views.upload_design_and_confirm, name='upload_design_and_confirm'),
    path('manual-create/', views.manual_order_create, name='manual_order_create'),
    path('check-customer/', views.check_customer_exists, name='check_customer_exists'),
    path('debug-upload/', views.debug_upload, name='debug_upload'),
]
