from django.contrib import admin
from .models import APISettings


@admin.register(APISettings)
class APISettingsAdmin(admin.ModelAdmin):
    list_display = ['name', 'google_drive_credentials_path', 'google_drive_parent_folder_id', 'updated_at']
    list_filter = ['updated_at']
    search_fields = ['name']
    ordering = ['-updated_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('name',)
        }),
        ('Google Drive 설정', {
            'fields': ('google_drive_credentials_path', 'google_drive_parent_folder_id')
        }),
        ('스마트스토어 설정', {
            'fields': ('smartstore_client_id', 'smartstore_client_secret')
        }),
    )
    
    def has_add_permission(self, request):
        # 이미 설정이 있으면 추가 불가
        return not APISettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # 삭제 불가
        return False