from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from datetime import datetime
import pandas as pd
from io import BytesIO
import os
from .models import Order, Status
from .forms import ManualOrderForm
from utils import calculate_business_days
from utils.google_drive import get_drive_service, upload_design_files
from utils.google_drive_oauth import get_oauth_service, upload_design_files_oauth
from utils.customer_utils import generate_customer_id, is_existing_customer
from django.conf import settings
from settings_app.models import APISettings


class OrderListView(LoginRequiredMixin, ListView):
    """주문 목록 조회"""
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 20
    ordering = ['-payment_date']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get('status')
        
        if status:
            queryset = queryset.filter(status=status)
        else:
            # 기본적으로 완료된 주문은 제외
            queryset = queryset.exclude(status=Status.COMPLETED)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', '')
        context['status_choices'] = Status.choices
        return context


class OrderDetailView(LoginRequiredMixin, DetailView):
    """주문 상세 조회"""
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_object()
        
        # 주문 항목들 가져오기
        context['order_items'] = order.items.all()
        
        # 주문 타입 판별
        context['is_general_order'] = order.is_general_order
        
        # 이전/다음 주문 링크
        context['prev_order'] = Order.objects.filter(
            payment_date__lt=order.payment_date
        ).order_by('-payment_date').first()
        
        context['next_order'] = Order.objects.filter(
            payment_date__gt=order.payment_date
        ).order_by('payment_date').first()
        
        return context


@login_required
@require_POST
def change_order_status(request):
    """주문 상태 변경"""
    order_id = request.POST.get('order_id')
    next_status = request.POST.get('next_status')
    
    if not order_id or not next_status:
        messages.error(request, '잘못된 요청입니다.')
        return redirect(request.META.get('HTTP_REFERER', '/orders/'))
    
    order = get_object_or_404(Order, id=order_id)
    
    # 상태 변경 로직
    if order.status == Status.NEW:
        if next_status == Status.CONSULTING:
            # 굿즈 주문의 경우 상담 시작
            order.status = Status.CONSULTING
            messages.success(request, f'주문 {order.smartstore_order_id}의 상담을 시작했습니다.')
        elif next_status == Status.PRODUCED:
            # 일반 주문의 경우 바로 발송 준비
            order.status = Status.PRODUCED
            messages.success(request, f'주문 {order.smartstore_order_id}를 발송 준비 상태로 변경했습니다.')
    
    elif order.status == Status.CONSULTING:
        if next_status == Status.PRODUCING:
            # 상담 완료, 제작 시작
            order.status = Status.PRODUCING
            order.confirmed_date = timezone.now()
            # 마감일 계산 (3 영업일 후)
            order.due_date = calculate_business_days(timezone.now(), 3)
            messages.success(request, f'주문 {order.smartstore_order_id}의 제작을 시작했습니다. 마감일: {order.due_date.strftime("%Y-%m-%d")}')
    
    elif order.status == Status.PRODUCING:
        if next_status == Status.PRODUCED:
            # 제작 완료
            order.status = Status.PRODUCED
            messages.success(request, f'주문 {order.smartstore_order_id}의 제작을 완료했습니다.')
    
    order.save()
    return redirect(request.META.get('HTTP_REFERER', '/orders/'))


@login_required
@require_POST
def export_shipping_excel(request):
    """발송 엑셀 출력 및 완료 처리"""
    order_ids = request.POST.getlist('order_ids')
    
    if not order_ids:
        messages.error(request, '선택된 주문이 없습니다.')
        return redirect(request.META.get('HTTP_REFERER', '/orders/'))
    
    orders = Order.objects.filter(id__in=order_ids, status=Status.PRODUCED)
    
    if not orders.exists():
        messages.error(request, '발송 준비 상태인 주문이 없습니다.')
        return redirect(request.META.get('HTTP_REFERER', '/orders/'))
    
    # 엑셀 데이터 생성
    data = []
    for order in orders:
        # 주문 제품 요약
        products_summary = []
        for item in order.items.all():
            products_summary.append(f"{item.smartstore_product_name} ({item.smartstore_option_text}) x{item.quantity}")
        
        data.append({
            '주문번호': order.smartstore_order_id,
            '고객명': order.customer_name,
            '연락처': order.customer_phone,
            '발송주소': order.shipping_address,
            '주문제품': ' | '.join(products_summary),
            '총금액': order.total_order_amount,
            '결제일': order.payment_date.strftime('%Y-%m-%d %H:%M'),
        })
    
    # DataFrame 생성
    df = pd.DataFrame(data)
    
    # 엑셀 파일 생성
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='발송목록', index=False)
    
    # 주문 상태를 COMPLETED로 변경
    orders.update(status=Status.COMPLETED)
    
    # 응답 생성
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="shipping_list_{timezone.now().strftime("%Y%m%d_%H%M")}.xlsx"'
    
    messages.success(request, f'{len(orders)}개 주문의 발송 목록을 출력하고 완료 처리했습니다.')
    return response


@login_required
@require_POST
def upload_design_and_confirm(request):
    """시안 파일 업로드 및 컨펌 완료 처리"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("=== 시안 업로드 시작 ===")
    logger.info(f"요청 메서드: {request.method}")
    logger.info(f"POST 데이터: {dict(request.POST)}")
    logger.info(f"FILES 데이터: {dict(request.FILES)}")
    logger.info(f"사용자: {request.user}")
    logger.info(f"요청 URL: {request.path}")
    logger.info(f"요청 헤더: {dict(request.META)}")
    
    
    order_id = request.POST.get('order_id')
    design_files = request.FILES.getlist('design_files')
    
    logger.info(f"주문 ID: {order_id}")
    logger.info(f"업로드 파일 개수: {len(design_files)}")
    
    if not order_id:
        logger.error("주문 ID가 없습니다.")
        messages.error(request, '주문 ID가 없습니다.')
        return redirect(request.META.get('HTTP_REFERER', '/orders/'))
    
    if not design_files:
        logger.error("업로드할 파일이 없습니다.")
        messages.error(request, '업로드할 파일을 선택해주세요.')
        return redirect(request.META.get('HTTP_REFERER', '/orders/'))
    
    try:
        order = get_object_or_404(Order, id=order_id)
        logger.info(f"주문 조회 성공: {order.smartstore_order_id}, 상태: {order.status}")
    except Exception as e:
        logger.error(f"주문 조회 실패: {e}")
        messages.error(request, f'주문을 찾을 수 없습니다: {str(e)}')
        return redirect(request.META.get('HTTP_REFERER', '/orders/'))
    
    if order.status != Status.CONSULTING:
        logger.error(f"잘못된 주문 상태: {order.status}")
        messages.error(request, '상담 중인 주문만 시안을 업로드할 수 있습니다.')
        return redirect(request.META.get('HTTP_REFERER', '/orders/'))
    
    try:
        logger.info("Google Drive 설정 확인 시작")
        
        # 환경 변수 확인 (배포 환경 우선)
        has_env_config = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON') and os.environ.get('GOOGLE_DRIVE_PARENT_FOLDER_ID')
        logger.info(f"환경 변수 설정 여부: {bool(has_env_config)}")
        
        # 환경 변수가 없으면 데이터베이스 설정 확인
        if not has_env_config:
            logger.info("API 설정 조회 시작")
            api_settings = APISettings.objects.first()
            logger.info(f"API 설정 조회 결과: {api_settings}")
        else:
            logger.info("환경 변수 사용 - 데이터베이스 설정 건너뜀")
            api_settings = None
        
        # Google Drive API 설정 확인
        if not has_env_config and (not api_settings or not api_settings.google_drive_credentials_path):
            logger.warning("Google Drive API 설정이 없습니다. 임시로 로컬 처리합니다.")
            
            # 주문 상태를 PRODUCING으로 변경 (Google Drive 없이)
            order.status = Status.PRODUCING
            order.confirmed_date = timezone.now()
            order.due_date = calculate_business_days(timezone.now(), 3).date()
            order.google_drive_folder_url = f"로컬_저장_{order.smartstore_order_id}"
            order.save()
            
            logger.info(f"주문 상태 변경 완료 - 상태: {order.status}, 마감일: {order.due_date}")
            
            messages.warning(
                request, 
                f'⚠️ Google Drive API 설정이 없어 로컬 처리되었습니다.<br>'
                f'시안 파일 {len(design_files)}개 업로드 완료<br>'
                f'주문이 제작 중 상태로 변경되었습니다.<br>'
                f'마감일: {order.due_date.strftime("%Y-%m-%d")}<br>'
                f'<strong>설정 페이지에서 Google Drive API를 설정해주세요.</strong>'
            )
            return redirect(request.META.get('HTTP_REFERER', '/orders/'))
        
        # Google Drive 폴더 ID 확인 (로컬 환경만)
        if not has_env_config:
            if not api_settings.google_drive_parent_folder_id or api_settings.google_drive_parent_folder_id == 'admin':
                logger.error(f"Google Drive 폴더 ID가 올바르지 않습니다: {api_settings.google_drive_parent_folder_id}")
                messages.error(
                    request,
                    f'⚠️ Google Drive 폴더 ID가 설정되지 않았습니다.<br>'
                    f'현재 값: "{api_settings.google_drive_parent_folder_id}"<br>'
                    f'설정 페이지에서 올바른 폴더 ID를 입력해주세요.<br>'
                    f'(Google Drive에서 폴더 우클릭 → 공유 → 링크에서 폴더 ID 복사)'
                )
                return redirect(request.META.get('HTTP_REFERER', '/orders/'))
            
            logger.info(f"로컬: Google Drive parent folder ID: {api_settings.google_drive_parent_folder_id}")
            logger.info(f"로컬: OAuth 사용 여부: {api_settings.use_oauth}")
        else:
            logger.info(f"배포: 환경 변수에서 폴더 ID 사용")
        
        # OAuth 또는 서비스 계정 선택 (로컬 환경만, 배포는 항상 Service Account)
        if not has_env_config and api_settings and api_settings.use_oauth and api_settings.oauth_credentials_path:
            logger.info("OAuth 2.0 방식 사용")
            logger.info(f"OAuth credentials path: {api_settings.oauth_credentials_path}")
            
            # 토큰 경로 설정 (없으면 기본 경로)
            if not api_settings.oauth_token_path:
                api_settings.oauth_token_path = os.path.join(settings.BASE_DIR, 'oauth_tokens', 'token.pickle')
                api_settings.save()
            
            logger.info(f"OAuth token path: {api_settings.oauth_token_path}")
            
            # OAuth 서비스 초기화
            logger.info("OAuth 서비스 초기화 시작")
            service = get_oauth_service(api_settings.oauth_credentials_path, api_settings.oauth_token_path)
            
            if not service:
                logger.error("OAuth 서비스 초기화 실패")
                messages.error(request, 'Google Drive OAuth 인증에 실패했습니다. OAuth Credentials 파일을 확인해주세요.')
                return redirect(request.META.get('HTTP_REFERER', '/orders/'))
            
            logger.info("OAuth 서비스 초기화 성공")
            
            # OAuth를 사용한 파일 업로드
            parent_folder_id = api_settings.google_drive_parent_folder_id
            logger.info(f"OAuth 파일 업로드 시작 - 주문ID: {order.smartstore_order_id}, 고객명: {order.customer_name}")
            
            upload_result = upload_design_files_oauth(
                service,
                design_files,
                order.smartstore_order_id,
                order.customer_name,
                parent_folder_id
            )
        else:
            logger.info("서비스 계정 방식 사용 (레거시)")
            logger.info(f"Google Drive credentials path: {api_settings.google_drive_credentials_path}")
            
            # 서비스 계정 서비스 초기화
            logger.info("Google Drive 서비스 초기화 시작")
            service = get_drive_service()
            if not service:
                logger.error("Google Drive 서비스 초기화 실패")
                messages.error(request, 'Google Drive 서비스에 연결할 수 없습니다. 설정을 확인해주세요.')
                return redirect(request.META.get('HTTP_REFERER', '/orders/'))
            
            logger.info("Google Drive 서비스 초기화 성공")
            
            # 서비스 계정을 사용한 파일 업로드
            parent_folder_id = api_settings.google_drive_parent_folder_id
            logger.info(f"파일 업로드 시작 - 주문ID: {order.smartstore_order_id}, 고객명: {order.customer_name}")
            
            upload_result = upload_design_files(
                service, 
                design_files, 
                order.smartstore_order_id, 
                order.customer_name,
                parent_folder_id
            )
        
        logger.info(f"업로드 결과: {upload_result}")
        
        # 임시 해결책: Google Drive 업로드 실패 시에도 로컬에 저장하고 상태 변경
        if upload_result and upload_result.get('folder'):
            logger.info("폴더 생성 성공 - 주문 상태 변경 시작")
            
            # 로컬에 파일 저장
            local_upload_dir = os.path.join(settings.BASE_DIR, 'uploads', 'designs', order.smartstore_order_id)
            os.makedirs(local_upload_dir, exist_ok=True)
            
            saved_files = []
            for design_file in design_files:
                file_path = os.path.join(local_upload_dir, design_file.name)
                with open(file_path, 'wb+') as destination:
                    for chunk in design_file.chunks():
                        destination.write(chunk)
                saved_files.append(design_file.name)
                logger.info(f"로컬 저장 완료: {file_path}")
            
            # 주문 상태를 PRODUCING으로 변경
            order.status = Status.PRODUCING
            order.confirmed_date = timezone.now()
            order.due_date = calculate_business_days(timezone.now(), 3).date()
            order.google_drive_folder_url = upload_result['folder']['webViewLink']
            order.save()
            
            logger.info(f"주문 상태 변경 완료 - 상태: {order.status}, 마감일: {order.due_date}")
            
            file_count = len(upload_result.get("files", []))
            if file_count > 0:
                messages.success(
                    request, 
                    f'✅ Google Drive에 시안 파일 {file_count}개가 업로드되었습니다!<br>'
                    f'주문이 <strong>제작 중</strong> 상태로 변경되었습니다.<br>'
                    f'마감일: <strong>{order.due_date.strftime("%Y-%m-%d")}</strong><br>'
                    f'<a href="{upload_result["folder"]["webViewLink"]}" target="_blank" class="btn btn-sm btn-primary">Google Drive 폴더 열기</a>'
                )
            else:
                messages.warning(
                    request, 
                    f'⚠️ Google Drive 폴더가 생성되었지만 파일 업로드에 실패했습니다.<br>'
                    f'파일은 로컬에 저장되었습니다: {len(saved_files)}개<br>'
                    f'저장 위치: <code>{local_upload_dir}</code><br>'
                    f'주문은 <strong>제작 중</strong> 상태로 변경되었습니다.<br>'
                    f'마감일: <strong>{order.due_date.strftime("%Y-%m-%d")}</strong><br>'
                    f'<a href="{upload_result["folder"]["webViewLink"]}" target="_blank" class="btn btn-sm btn-primary">Google Drive 폴더 열기</a><br>'
                    f'<small class="text-muted">파일을 수동으로 Google Drive에 업로드해주세요.</small>'
                )
        else:
            logger.error("폴더 생성 실패")
            messages.error(request, 'Google Drive 폴더 생성에 실패했습니다.')
            
    except Exception as e:
        logger.error(f"시안 업로드 중 예외 발생: {str(e)}", exc_info=True)
        messages.error(request, f'시안 업로드 중 오류가 발생했습니다: {str(e)}')
    
    logger.info("=== 시안 업로드 완료 ===")
    return redirect(request.META.get('HTTP_REFERER', '/orders/'))


@login_required
def manual_order_create(request):
    """수동 주문 등록"""
    if request.method == 'POST':
        form = ManualOrderForm(request.POST)
        if form.is_valid():
            try:
                order = form.save()
                messages.success(
                    request, 
                    f'수동 주문이 성공적으로 등록되었습니다. 주문번호: {order.smartstore_order_id}'
                )
                return redirect('order_list')
            except Exception as e:
                messages.error(request, f'주문 등록 중 오류가 발생했습니다: {str(e)}')
    else:
        form = ManualOrderForm()
    
    return render(request, 'orders/manual_order_form.html', {
        'form': form,
        'title': '수동 주문 등록'
    })


@login_required
def check_customer_exists(request):
    """고객 존재 여부 확인 (AJAX)"""
    if request.method == 'GET':
        customer_name = request.GET.get('customer_name', '')
        customer_phone = request.GET.get('customer_phone', '')
        
        if customer_name and customer_phone:
            exists = is_existing_customer(customer_name, customer_phone)
            generated_id = generate_customer_id(customer_name, customer_phone)
            
            return HttpResponse(
                f'{{"exists": {str(exists).lower()}, "generated_id": "{generated_id}"}}',
                content_type='application/json'
            )
    
    return HttpResponse('{"error": "Invalid request"}', content_type='application/json')


@login_required
def debug_upload(request):
    """시안 업로드 디버깅 페이지"""
    return render(request, 'orders/debug_upload.html')