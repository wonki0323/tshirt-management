"""
Google Drive OAuth 2.0 연동 유틸리티
"""
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import logging

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/drive.file']


def get_oauth_service(credentials_path, token_path):
    """
    OAuth 2.0을 사용하여 Google Drive API 서비스 객체를 생성합니다.
    
    Args:
        credentials_path: OAuth 2.0 클라이언트 credentials JSON 파일 경로
        token_path: 토큰을 저장할 pickle 파일 경로
    
    Returns:
        Google Drive API service 객체
    """
    creds = None
    
    try:
        logger.info(f"OAuth 서비스 생성 시작")
        logger.info(f"Credentials 경로: {credentials_path}")
        logger.info(f"Credentials 경로 타입: {type(credentials_path)}")
        logger.info(f"Credentials 경로 repr: {repr(credentials_path)}")
        logger.info(f"Token 경로: {token_path}")
        
        # 경로 공백 제거
        credentials_path = credentials_path.strip()
        token_path = token_path.strip()
        
        logger.info(f"정리된 Credentials 경로: {credentials_path}")
        logger.info(f"정리된 Token 경로: {token_path}")
        
        # 파일 존재 확인
        if not os.path.exists(credentials_path):
            logger.error(f"❌ OAuth Credentials 파일이 존재하지 않습니다: {credentials_path}")
            return None
        
        logger.info(f"✅ OAuth Credentials 파일 존재 확인")
        
        # 토큰 파일이 있으면 로드
        if os.path.exists(token_path):
            logger.info("기존 토큰 파일 로드 시도")
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
            logger.info("토큰 파일 로드 성공")
        
        # 토큰이 없거나 유효하지 않으면 새로 받기
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("토큰 갱신 시도")
                creds.refresh(Request())
                logger.info("토큰 갱신 성공")
            else:
                logger.info("새 토큰 발급 필요 - 브라우저 인증 시작")
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
                logger.info("브라우저 인증 완료")
            
            # 토큰 저장
            os.makedirs(os.path.dirname(token_path), exist_ok=True)
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
            logger.info(f"토큰 저장 완료: {token_path}")
        
        # Drive API 서비스 빌드
        logger.info("Google Drive API 서비스 빌드 시작")
        service = build('drive', 'v3', credentials=creds)
        logger.info("Google Drive API 서비스 빌드 성공")
        
        return service
        
    except Exception as e:
        logger.error(f"OAuth 서비스 생성 실패: {e}", exc_info=True)
        return None


def create_folder_oauth(service, folder_name, parent_folder_id=None):
    """OAuth를 사용하여 Google Drive에 폴더를 생성합니다."""
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
            fields='id,name,webViewLink'
        ).execute()
        
        logger.info(f"폴더 생성 완료: {folder['id']}")
        
        # 폴더에 공개 읽기 권한 설정
        permission = {
            'type': 'anyone',
            'role': 'reader'
        }
        
        service.permissions().create(
            fileId=folder['id'],
            body=permission
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


def upload_file_oauth(service, file_obj, folder_id, file_name):
    """OAuth를 사용하여 파일을 Google Drive에 업로드합니다."""
    try:
        logger.info(f"파일 업로드 시작: {file_name}")
        
        # 파일 내용 읽기
        file_content = file_obj.read()
        logger.info(f"파일 읽기 완료 - 크기: {len(file_content)} bytes")
        file_obj.seek(0)
        
        # 파일 타입 확인
        content_type = getattr(file_obj, 'content_type', None) or 'application/octet-stream'
        logger.info(f"Content-Type: {content_type}")
        
        media = MediaIoBaseUpload(
            io.BytesIO(file_content),
            mimetype=content_type,
            resumable=True
        )
        
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        
        logger.info("Google Drive API 호출 시작")
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,name,webViewLink'
        ).execute()
        
        logger.info(f"파일 업로드 성공: {file['id']}")
        
        return {
            'id': file['id'],
            'name': file['name'],
            'webViewLink': file['webViewLink']
        }
        
    except Exception as e:
        logger.error(f"파일 업로드 중 오류 발생: {e}", exc_info=True)
        return None


def upload_design_files_oauth(service, files, order_id, customer_name, parent_folder_id=None):
    """OAuth를 사용하여 주문에 대한 시안 파일들을 업로드합니다."""
    try:
        logger.info(f"OAuth 시안 파일 업로드 시작 - 주문ID: {order_id}, 고객명: {customer_name}, 파일수: {len(files)}")
        
        # 주문별 폴더 생성
        folder_name = f"[{order_id}]_{customer_name}"
        logger.info(f"폴더 생성 시작 - 폴더명: {folder_name}")
        
        folder_info = create_folder_oauth(service, folder_name, parent_folder_id)
        logger.info(f"폴더 생성 결과: {folder_info}")
        
        if not folder_info:
            logger.error("폴더 생성 실패")
            return None
        
        uploaded_files = []
        
        # 각 파일을 폴더에 업로드
        for i, file in enumerate(files):
            logger.info(f"파일 {i+1}/{len(files)} 업로드 시작 - 파일명: {file.name}, 크기: {file.size}")
            file_info = upload_file_oauth(service, file, folder_info['id'], file.name)
            if file_info:
                uploaded_files.append(file_info)
                logger.info(f"파일 {i+1} 업로드 성공: {file_info}")
            else:
                logger.error(f"파일 {i+1} 업로드 실패: {file.name}")
        
        result = {
            'folder': folder_info,
            'files': uploaded_files
        }
        logger.info(f"전체 업로드 완료 - 성공: {len(uploaded_files)}/{len(files)}개")
        return result
        
    except Exception as e:
        logger.error(f"OAuth 시안 파일 업로드 실패: {e}", exc_info=True)
        return None

