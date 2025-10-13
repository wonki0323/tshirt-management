from django.db import models


class APISettings(models.Model):
    """API 키 및 설정 관리"""
    name = models.CharField(max_length=100, unique=True, verbose_name="설정명")
    google_drive_credentials_path = models.CharField(
        max_length=500, 
        blank=True, 
        null=True,
        verbose_name="Google Drive 서비스 계정 키 파일 경로"
    )
    google_drive_parent_folder_id = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="Google Drive 상위 폴더 ID"
    )
    
    # OAuth 2.0 설정
    use_oauth = models.BooleanField(
        default=False,
        verbose_name="OAuth 2.0 사용"
    )
    oauth_credentials_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="OAuth 2.0 Credentials JSON 파일 경로"
    )
    oauth_token_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="OAuth 2.0 토큰 저장 경로"
    )
    
    smartstore_client_id = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name="스마트스토어 클라이언트 ID"
    )
    smartstore_client_secret = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name="스마트스토어 클라이언트 시크릿"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")

    class Meta:
        verbose_name = "API 설정"
        verbose_name_plural = "API 설정"
        ordering = ['-updated_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # 첫 번째 설정만 유지
        if not self.pk and APISettings.objects.exists():
            existing = APISettings.objects.first()
            existing.delete()
        super().save(*args, **kwargs)