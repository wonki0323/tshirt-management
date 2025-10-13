# 커스텀 티셔츠 판매 관리 시스템

스마트스토어 주문을 관리하고, 제작 워크플로우를 추적하며, 정확한 순이익을 계산하는 Django 웹 애플리케이션입니다.

## 기술 스택

- **Backend**: Python, Django Framework
- **Database**: PostgreSQL (개발 초기에는 SQLite 사용)
- **UI**: Django Templates (Bootstrap 추후 적용)
- **External APIs**: Naver Smartstore API, Google Drive API

## 프로젝트 구조

```
tshirt_management/
├── manage.py
├── requirements.txt
├── .env
├── db.sqlite3
├── tshirt_management/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── products/          # 제품 정보 및 옵션별 원가 관리
├── orders/           # 주문 수집, 워크플로우 관리, 시안 관리
└── finance/          # 지출 관리 및 재무 리포트
```

## 설치 및 실행

### 1. 가상환경 활성화
```bash
source tshirt_management_env/bin/activate
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 편집하여 필요한 API 키들을 설정하세요
```

### 4. 데이터베이스 마이그레이션
```bash
python manage.py migrate
```

### 5. 슈퍼유저 생성 (이미 생성됨)
```bash
python manage.py createsuperuser
```

### 6. 테스트 데이터 생성 (선택사항)
```bash
python manage.py generate_test_data --clear
```

### 7. 개발 서버 실행
```bash
python manage.py runserver
```

## 접속 정보

### 로그인 페이지
- URL: http://127.0.0.1:8000/
- 사용자명: `admin`
- 비밀번호: `admin123`

### 대시보드
- URL: http://127.0.0.1:8000/dashboard/
- 로그인 후 자동으로 이동됩니다

### 관리자 페이지
- URL: http://127.0.0.1:8000/admin/
- 사용자명: `admin`
- 비밀번호: `admin123`

## 주요 기능

### 1. 제품 관리 (products 앱)
- **Product**: 기본 제품 정보 (예: 라운드 반팔 티셔츠)
- **ProductOption**: 세부 옵션 및 원가 관리 (예: 화이트 / L 사이즈)

### 2. 주문 관리 (orders 앱)
- **Order**: 주문 기본 정보 및 워크플로우 상태 관리
- **OrderItem**: 주문 상세 항목 및 원가 추적
- **Status**: 주문 처리 워크플로우 상태
  - NEW: 신규 주문
  - CONSULTING: 상담/시안 제작 중
  - CONFIRMED: 고객 컨펌 완료
  - PRODUCING: 제작 중
  - PRODUCED: 제작 완료
  - SHIPPED: 발송 완료
  - COMPLETED: 정산 완료
  - CANCELED: 주문 취소

### 3. 재무 관리 (finance 앱)
- **Expense**: 지출 내역 관리 (배송비, 광고비, 재료비 등)

## 데이터베이스 설정

### 개발 환경 (SQLite)
현재 `.env` 파일에서 SQLite를 사용하도록 설정되어 있습니다.

### 프로덕션 환경 (PostgreSQL)
`.env` 파일에서 다음 설정을 변경하세요:
```
DATABASE_URL=postgresql://username:password@localhost:5432/tshirt_management
```

## API 키 설정

`.env` 파일에 다음 API 키들을 추가하세요:
```
NAVER_SMARTSTORE_API_KEY=your_api_key_here
GOOGLE_DRIVE_API_KEY=your_api_key_here
```

## 주요 특징

1. **정확한 원가 추적**: 주문 시점의 원가를 복사하여 저장하여 정확한 순이익 계산
2. **워크플로우 관리**: 8단계 주문 처리 상태로 체계적인 주문 관리
3. **다중 제품 주문 지원**: 하나의 주문에 여러 제품 항목 처리 가능
4. **구글 드라이브 연동**: 시안/원본 이미지 통합 관리
5. **재무 리포트**: 지출 관리 및 순이익 계산

## 새로운 기능

### 🔐 인증 시스템
- 모든 페이지에 로그인 필수
- 루트 URL(`/`)은 로그인 페이지로 리다이렉트
- 대시보드는 `/dashboard/`에서 접근

### 📊 고도화된 대시보드
- **정확한 재무 계산**: CANCELED 주문 제외, Django ORM Aggregation 사용
- **클릭 가능한 통계**: 각 카드 클릭 시 상세 목록 페이지로 이동
- **실시간 데이터**: 데이터베이스의 실제 데이터를 기반으로 실시간 계산

### 📋 상세 목록 페이지
- **주문 관리**: `/orders/` - 상태별 필터링 지원
- **제품 관리**: `/products/` - 제품별 옵션 표시
- **지출 관리**: `/finance/expenses/` - 카테고리별 지출 내역

### 🔧 관리 명령어
```bash
# 테스트 데이터 생성
python manage.py generate_test_data --clear

# 스마트스토어 동기화 (기본 구조)
python manage.py sync_smartstore --days 7
```

### 🌐 API 연동 준비
- `.env.example` 파일로 환경 변수 관리
- 네이버 스마트스토어 API 설정
- 구글 드라이브 API 설정

## 다음 단계

1. 스마트스토어 API 실제 연동 구현
2. 구글 드라이브 API 실제 연동 구현
3. 자동 마감일 계산 로직
4. 엑셀 출력 기능
5. 이메일 알림 기능
6. 모바일 반응형 UI 개선
