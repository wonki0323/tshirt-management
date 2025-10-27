"""
Google Drive OAuth 2.0 연동 유틸리티
"""
import os
import json
import pickle
import base64
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import logging

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/drive.file']


def get_oauth_service(credentials_path=None, token_path=None):
    """
    OAuth 2.0을 사용하여 Google Drive API 서비스 객체를 생성합니다.
    
    Args:
        credentials_path: OAuth 2.0 클라이언트 credentials JSON 파일 경로 (선택)
        token_path: 토큰을 저장할 pickle 파일 경로 (선택)
    
    Returns:
        Google Drive API service 객체
    """
    creds = None
    
    try:
        logger.info(f"OAuth 서비스 생성 시작")
        
        # 환경 변수에서 토큰 읽기 (배포 환경 우선)
        # JSON 형식 우선 확인 (client_id, client_secret 포함)
        token_json_base64 = os.environ.get('GOOGLE_OAUTH_TOKEN_JSON')
        token_base64 = os.environ.get('GOOGLE_OAUTH_TOKEN_BASE64')
        
        # 환경 변수로 각 필드 직접 전달 (가장 안전한 방법)
        token_value = os.environ.get('GOOGLE_OAUTH_ACCESS_TOKEN')
        refresh_token_value = os.environ.get('GOOGLE_OAUTH_REFRESH_TOKEN')
        client_id_value = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
        client_secret_value = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
        
        if all([refresh_token_value, client_id_value, client_secret_value]):
            logger.info("환경 변수에서 OAuth 토큰 로드 (개별 필드)")
            try:
                from google.oauth2.credentials import Credentials
                creds = Credentials(
                    token=token_value,
                    refresh_token=refresh_token_value,
                    token_uri='https://oauth2.googleapis.com/token',
                    client_id=client_id_value,
                    client_secret=client_secret_value,
                    scopes=['https://www.googleapis.com/auth/drive.file']
                )
                logger.info("환경 변수에서 개별 필드 토큰 로드 성공")
            except Exception as e:
                logger.error(f"개별 필드 토큰 생성 실패: {e}")
                creds = None
        elif token_json_base64:
            logger.info("환경 변수에서 OAuth 토큰 로드 (JSON 형식)")
            try:
                # Base64 디코딩 (공백과 줄바꿈 제거)
                token_json_base64_clean = token_json_base64.strip().replace('\n', '').replace('\r', '').replace(' ', '')
                logger.info(f"Base64 토큰 길이: {len(token_json_base64_clean)}")
                
                token_json_str = base64.b64decode(token_json_base64_clean).decode('utf-8')
                logger.info(f"디코딩된 JSON 길이: {len(token_json_str)}")
                
                token_dict = json.loads(token_json_str)
                
                # JSON에서 Credentials 객체 생성
                from google.oauth2.credentials import Credentials
                creds = Credentials(
                    token=token_dict.get('token'),
                    refresh_token=token_dict.get('refresh_token'),
                    token_uri=token_dict.get('token_uri'),
                    client_id=token_dict.get('client_id'),
                    client_secret=token_dict.get('client_secret'),
                    scopes=token_dict.get('scopes')
                )
                logger.info("환경 변수에서 JSON 토큰 로드 성공")
            except Exception as e:
                logger.error(f"JSON 토큰 파싱 실패: {e}")
                creds = None
        elif token_base64:
            logger.info("환경 변수에서 OAuth 토큰 로드 (Pickle 형식)")
            try:
                token_data = base64.b64decode(token_base64)
                creds = pickle.loads(token_data)
                logger.info("환경 변수에서 Pickle 토큰 로드 성공")
            except Exception as e:
                logger.error(f"Pickle 토큰 파싱 실패: {e}")
                creds = None
        elif token_path and os.path.exists(token_path):
            # 로컬 환경: 파일에서 토큰 로드
            logger.info(f"로컬: 토큰 파일에서 로드 - {token_path}")
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
            logger.info("토큰 파일 로드 성공")
        
        if not creds:
            logger.info("토큰이 없음 - 새로 인증 필요")
            
            # credentials 파일 확인
            if not credentials_path or not os.path.exists(credentials_path):
                logger.error(f"❌ OAuth Credentials 파일이 존재하지 않습니다: {credentials_path}")
                return None
            
            logger.info(f"✅ OAuth Credentials 파일 존재 확인: {credentials_path}")
        
        # 토큰이 없거나 유효하지 않으면 갱신 시도
        if creds and not creds.valid:
            if creds.expired and creds.refresh_token:
                logger.info("토큰 만료 - 갱신 시도")
                try:
                    creds.refresh(Request())
                    logger.info("토큰 갱신 성공")
                    
                    # 갱신된 토큰 저장 (로컬 환경만)
                    if token_path:
                        os.makedirs(os.path.dirname(token_path), exist_ok=True)
                        with open(token_path, 'wb') as token:
                            pickle.dump(creds, token)
                        logger.info(f"갱신된 토큰 저장 완료: {token_path}")
                    
                    # 배포 환경에서 토큰 갱신된 경우 로그 출력
                    if token_json_base64 or token_base64:
                        logger.warning("⚠️ 배포 환경에서 토큰이 갱신되었습니다. 새 토큰을 환경 변수에 업데이트해야 합니다!")
                        # JSON 형식으로 출력
                        token_dict = {
                            'token': creds.token,
                            'refresh_token': creds.refresh_token,
                            'token_uri': creds.token_uri,
                            'client_id': creds.client_id,
                            'client_secret': creds.client_secret,
                            'scopes': creds.scopes,
                        }
                        token_json = json.dumps(token_dict)
                        token_json_base64_new = base64.b64encode(token_json.encode()).decode()
                        logger.warning(f"갱신된 토큰 (JSON Base64, 처음 100자): {token_json_base64_new[:100]}...")
                        
                except Exception as refresh_error:
                    logger.error(f"토큰 갱신 중 오류 발생: {refresh_error}")
                    # 로컬에서만 새 인증 시도
                    if credentials_path and os.path.exists(credentials_path):
                        logger.info("새 토큰 발급 필요 - 브라우저 인증 시작")
                        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                        creds = flow.run_local_server(port=0)
                        logger.info("브라우저 인증 완료")
                        
                        # 토큰 저장
                        if token_path:
                            os.makedirs(os.path.dirname(token_path), exist_ok=True)
                            with open(token_path, 'wb') as token:
                                pickle.dump(creds, token)
                            logger.info(f"토큰 저장 완료: {token_path}")
                    else:
                        logger.error("배포 환경에서 토큰 갱신 실패 - 새로운 토큰이 필요합니다")
                        return None
            else:
                logger.error("토큰 갱신 실패 - refresh_token 없음")
                # 로컬에서만 새 인증 시도
                if credentials_path and os.path.exists(credentials_path):
                    logger.info("새 토큰 발급 필요 - 브라우저 인증 시작")
                    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                    logger.info("브라우저 인증 완료")
                    
                    # 토큰 저장
                    if token_path:
                        os.makedirs(os.path.dirname(token_path), exist_ok=True)
                        with open(token_path, 'wb') as token:
                            pickle.dump(creds, token)
                        logger.info(f"토큰 저장 완료: {token_path}")
                else:
                    logger.error("배포 환경에서 토큰 갱신 실패 - 새로운 토큰이 필요합니다")
                    return None
        
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

