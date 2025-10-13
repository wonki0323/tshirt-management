"""
환경 변수에서 Google Drive 서비스를 초기화하는 유틸리티
"""
import os
import json
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/drive.file']


def get_drive_service_from_env():
    """
    환경 변수에서 Google Drive Service Account credentials를 읽어 서비스를 초기화합니다.
    
    Returns:
        Google Drive API service 객체 또는 None
    """
    try:
        # 환경 변수에서 credentials JSON 읽기
        credentials_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
        
        if not credentials_json:
            logger.warning("GOOGLE_SERVICE_ACCOUNT_JSON 환경 변수가 설정되지 않았습니다.")
            return None
        
        # JSON 파싱
        credentials_info = json.loads(credentials_json)
        
        # Service Account credentials 생성
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=SCOPES
        )
        
        # Drive API 서비스 빌드
        service = build('drive', 'v3', credentials=credentials)
        logger.info("Google Drive 서비스 초기화 성공 (환경 변수)")
        
        return service
        
    except json.JSONDecodeError as e:
        logger.error(f"GOOGLE_SERVICE_ACCOUNT_JSON 파싱 오류: {e}")
        return None
    except Exception as e:
        logger.error(f"Google Drive 서비스 초기화 실패: {e}", exc_info=True)
        return None


def upload_design_files_env(design_files, order_id, customer_name):
    """
    환경 변수로 초기화된 서비스를 사용하여 파일을 업로드합니다.
    
    Args:
        design_files: 업로드할 파일 리스트
        order_id: 주문 ID
        customer_name: 고객명
    
    Returns:
        업로드 결과 딕셔너리 또는 None
    """
    try:
        # 서비스 초기화
        service = get_drive_service_from_env()
        if not service:
            logger.error("Google Drive 서비스 초기화 실패")
            return None
        
        # 상위 폴더 ID 가져오기
        parent_folder_id = os.environ.get('GOOGLE_DRIVE_PARENT_FOLDER_ID')
        if not parent_folder_id:
            logger.error("GOOGLE_DRIVE_PARENT_FOLDER_ID 환경 변수가 설정되지 않았습니다.")
            return None
        
        # 폴더 이름 생성
        folder_name = f"[{order_id}]_{customer_name}"
        
        # 폴더 생성
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_folder_id]
        }
        
        folder = service.files().create(
            body=folder_metadata,
            fields='id,name,webViewLink',
            supportsAllDrives=True
        ).execute()
        
        logger.info(f"폴더 생성 성공: {folder['name']} ({folder['id']})")
        
        # 파일 업로드
        uploaded_files = []
        for design_file in design_files:
            file_metadata = {
                'name': design_file.name,
                'parents': [folder['id']]
            }
            
            media = MediaIoBaseUpload(
                design_file,
                mimetype=design_file.content_type,
                resumable=True
            )
            
            uploaded_file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink',
                supportsAllDrives=True
            ).execute()
            
            uploaded_files.append({
                'id': uploaded_file['id'],
                'name': uploaded_file['name'],
                'webViewLink': uploaded_file['webViewLink']
            })
            
            logger.info(f"파일 업로드 성공: {uploaded_file['name']}")
        
        return {
            'folder': {
                'id': folder['id'],
                'name': folder['name'],
                'webViewLink': folder['webViewLink']
            },
            'files': uploaded_files
        }
        
    except Exception as e:
        logger.error(f"파일 업로드 실패: {e}", exc_info=True)
        return None

