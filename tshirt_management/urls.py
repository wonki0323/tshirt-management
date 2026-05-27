"""
URL configuration for tshirt_management project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from . import views
from popbill_api import bankda_views

def redirect_to_login(request):
    return redirect('/login/')

urlpatterns = [
    path('', redirect_to_login, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('orders/', include('orders.urls')),
    path('products/', include('products.urls')),
    path('finance/', include('finance.urls')),
    path('settings/', include('settings_app.urls')),
    path('popbill/', include('popbill_api.urls')),

    # 뱅크다 자동입금확인 webhook (방식 A, 2026-05-25) — 외부 호출이라 root 경로
    path('bankda/unconfirmed-orders/', bankda_views.unconfirmed_orders_list, name='bankda_unconfirmed_orders'),
    path('bankda/order-detail/', bankda_views.order_detail, name='bankda_order_detail'),
    path('bankda/payment-confirm/', bankda_views.payment_confirm, name='bankda_payment_confirm'),

    # 운영자용 — 잘못 자동매칭된 입금 되돌리기 (2026-05-27)
    path('bankda/rollback/<int:pk>/', bankda_views.rollback_deposit, name='bankda_rollback'),

    path('admin/', admin.site.urls),
]

# 개발 환경에서 미디어 파일 서빙
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
