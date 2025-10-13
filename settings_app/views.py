from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import APISettings


@login_required
def api_settings(request):
    """API 설정 페이지"""
    try:
        settings_obj = APISettings.objects.first()
    except APISettings.DoesNotExist:
        settings_obj = None
    
    if request.method == 'POST':
        if settings_obj:
            # 기존 설정 업데이트
            settings_obj.name = request.POST.get('name', 'API 설정')
            settings_obj.use_oauth = request.POST.get('use_oauth') == 'on'
            settings_obj.oauth_credentials_path = request.POST.get('oauth_credentials_path', '')
            settings_obj.google_drive_credentials_path = request.POST.get('google_drive_credentials_path', '')
            settings_obj.google_drive_parent_folder_id = request.POST.get('google_drive_parent_folder_id', '')
            settings_obj.smartstore_client_id = request.POST.get('smartstore_client_id', '')
            settings_obj.smartstore_client_secret = request.POST.get('smartstore_client_secret', '')
            settings_obj.save()
            messages.success(request, 'API 설정이 성공적으로 업데이트되었습니다.')
        else:
            # 새 설정 생성
            APISettings.objects.create(
                name=request.POST.get('name', 'API 설정'),
                use_oauth=request.POST.get('use_oauth') == 'on',
                oauth_credentials_path=request.POST.get('oauth_credentials_path', ''),
                google_drive_credentials_path=request.POST.get('google_drive_credentials_path', ''),
                google_drive_parent_folder_id=request.POST.get('google_drive_parent_folder_id', ''),
                smartstore_client_id=request.POST.get('smartstore_client_id', ''),
                smartstore_client_secret=request.POST.get('smartstore_client_secret', '')
            )
            messages.success(request, 'API 설정이 성공적으로 생성되었습니다.')
        
        return redirect('api_settings')
    
    context = {
        'settings': settings_obj
    }
    return render(request, 'settings_app/api_settings.html', context)