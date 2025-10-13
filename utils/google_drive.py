"""
Google Drive API 연동 유틸리티
"""
import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from django.conf import settings
import io


def get_drive_service():
    """Google Drive API 서비스 객체를 생성하고 반환합니다."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Google Drive 서비스 생성 시작")
        
        # 환경 변수에서 Service Account JSON 읽기 (배포 환경)
        service_account_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
        
        if service_account_json:
            logger.info("환경 변수에서 Service Account credentials 로드")
            try:
                credentials_info = json.loads(service_account_json)
                credentials = service_account.Credentials.from_service_account_info(
                    credentials_info,
                    scopes=['https://www.googleapis.com/auth/drive.file']
                )
                logger.info("환경 변수에서 credentials 생성 성공")
            except json.JSONDecodeError as e:
                logger.error(f"JSON 파싱 오류: {e}")
                return None
        else:
            # 로컬 환경: 파일에서 읽기
            logger.info("로컬 환경: 파일에서 credentials 로드")
            from settings_app.models import APISettings
            
            api_settings = APISettings.objects.first()
            logger.info(f"API 설정 조회: {api_settings}")
            
            if not api_settings or not api_settings.google_drive_credentials_path:
                logger.error("Google Drive credentials path not configured")
                return None
            
            credentials_path = api_settings.google_drive_credentials_path
            logger.info(f"Credentials 파일 경로: {credentials_path}")
            
            if not os.path.exists(credentials_path):
                logger.error(f"Google Drive credentials file not found: {credentials_path}")
                return None
            
            logger.info("Credentials 파일 로드 시작")
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
            logger.info("Credentials 파일 로드 성공")
        
        logger.info("Google Drive API 서비스 빌드 시작")
        service = build('drive', 'v3', credentials=credentials)
        logger.info("Google Drive API 서비스 빌드 성공")
        
        return service
    except Exception as e:
        logger.error(f"Error creating Google Drive service: {e}", exc_info=True)
        return None


def create_folder(service, folder_name, parent_folder_id=None):
    """지정된 상위 폴더 아래에 새 폴더를 생성하고 폴더 정보를 반환합니다."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"폴더 생성 시작: {folder_name}")
        
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        if parent_folder_id:
            folder_metadata['parents'] = [parent_folder_id]
        
        folder = service.files().create(
            body=folder_metadata,
            fields='id,name,webViewLink',
            supportsAllDrives=True  # 공유 드라이브 지원
        ).execute()
        
        logger.info(f"폴더 생성 완료: {folder['id']}")
        
        # 폴더에 공개 읽기 권한 설정
        permission = {
            'type': 'anyone',
            'role': 'reader'
        }
        
        service.permissions().create(
            fileId=folder['id'],
            body=permission,
            supportsAllDrives=True
        ).execute()
        
        logger.info("폴더 권한 설정 완료")
        
        return {
            'id': folder['id'],
            'name': folder['name'],
            'webViewLink': folder['webViewLink']
        }
    except Exception as e:
        logger.error(f"폴더 생성 중 오류 발생: {e}", exc_info=True)
        return None


def upload_file(service, file_obj, folder_id, file_name):
    """Django 파일 객체를 Google Drive 폴더에 업로드합니다."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"파일 업로드 시작 - 파일명: {file_name}, 폴더ID: {folder_id}")
        
        # 파일 내용을 메모리로 읽기
        file_content = file_obj.read()
        logger.info(f"파일 읽기 완료 - 크기: {len(file_content)} bytes")
        file_obj.seek(0)  # 파일 포인터를 처음으로 되돌리기
        
        # 파일 타입 확인
        content_type = getattr(file_obj, 'content_type', None) or 'application/octet-stream'
        logger.info(f"Content-Type: {content_type}")
        
        media = MediaIoBaseUpload(
            io.BytesIO(file_content),
            mimetype=content_type,
            resumable=True
        )
        logger.info("MediaIoBaseUpload 객체 생성 완료")
        
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        logger.info(f"파일 메타데이터: {file_metadata}")
        
        logger.info("Google Drive API 호출 시작")
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,name,webViewLink',
            supportsAllDrives=True  # 공유 드라이브 지원
        ).execute()
        logger.info(f"파일 업로드 완료: {file}")
        
        return {
            'id': file['id'],
            'name': file['name'],
            'webViewLink': file['webViewLink']
        }
    except Exception as e:
        logger.error(f"파일 업로드 중 오류 발생: {e}", exc_info=True)
        return None


def upload_design_files(service, files, order_id, customer_name, parent_folder_id=None):
    """주문에 대한 시안 파일들을 업로드합니다."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"시안 파일 업로드 시작 - 주문ID: {order_id}, 고객명: {customer_name}, 파일수: {len(files)}")
        
        # parent_folder_id가 없으면 환경 변수에서 읽기
        if not parent_folder_id:
            parent_folder_id = os.environ.get('GOOGLE_DRIVE_PARENT_FOLDER_ID')
            logger.info(f"환경 변수에서 폴더 ID 읽기: {parent_folder_id}")
        
        # 주문별 폴더 생성
        folder_name = f"[{order_id}]_{customer_name}"
        logger.info(f"폴더 생성 시작 - 폴더명: {folder_name}, 상위폴더ID: {parent_folder_id}")
        
        folder_info = create_folder(service, folder_name, parent_folder_id)
        logger.info(f"폴더 생성 결과: {folder_info}")
        
        if not folder_info:
            logger.error("폴더 생성 실패")
            return None
        
        uploaded_files = []
        
        # 각 파일을 폴더에 업로드
        for i, file in enumerate(files):
            logger.info(f"파일 {i+1}/{len(files)} 업로드 시작 - 파일명: {file.name}, 크기: {file.size}")
            file_info = upload_file(service, file, folder_info['id'], file.name)
            if file_info:
                uploaded_files.append(file_info)
                logger.info(f"파일 {i+1} 업로드 성공: {file_info}")
            else:
                logger.error(f"파일 {i+1} 업로드 실패: {file.name}")
        
        result = {
            'folder': folder_info,
            'files': uploaded_files
        }
        logger.info(f"전체 업로드 완료 - 결과: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error uploading design files: {e}", exc_info=True)
        return None
