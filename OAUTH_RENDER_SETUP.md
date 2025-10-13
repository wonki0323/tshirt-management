# 🚀 OAuth 2.0 Render 배포 설정 가이드

## ✅ OAuth 방식의 장점

- **Service Account 권한 문제 해결**: 본인 계정이므로 Google Drive 전체 권한 자동 부여
- **안정적인 파일 업로드**: 폴더 생성 + 파일 업로드 모두 성공
- **내부용으로 완벽**: 한 번만 인증하면 계속 사용 가능

---

## 📋 Render 환경 변수 설정

### **Step 1: Render 대시보드 접속**

1. https://dashboard.render.com 로그인
2. `tshirt-management-web` 서비스 클릭
3. 좌측 메뉴에서 **Environment** 클릭

---

### **Step 2: 환경 변수 추가**

다음 환경 변수를 **추가**하세요:

#### **1. OAuth 토큰 (필수)**

**Key:**
```
GOOGLE_OAUTH_TOKEN_BASE64
```

**Value:** (아래 명령어로 생성한 토큰을 복사)
```bash
cd /Users/wonkikim
python3 -c "
import pickle
import base64

with open('oauth_tokens/token.pickle', 'rb') as f:
    token_data = f.read()

encoded = base64.b64encode(token_data).decode('utf-8')
print(encoded)
"
```

위 명령어 실행 결과를 **전체 복사**하여 Value에 붙여넣기

---

#### **2. Google Drive 폴더 ID (이미 설정되어 있음)**

**Key:**
```
GOOGLE_DRIVE_PARENT_FOLDER_ID
```

**Value:**
```
10N9KznM6kJRTa7wBilZG_Lb2nLCvnhxF
```

✅ **이미 설정되어 있으면 건드리지 마세요!**

---

#### **3. Service Account 환경 변수 삭제 (선택)**

OAuth를 사용하므로 Service Account 관련 환경 변수는 **삭제해도** 됩니다:
- ❌ `GOOGLE_SERVICE_ACCOUNT_JSON` (삭제 가능)

**하지만 백업용으로 남겨두는 것도 좋습니다.**

---

### **Step 3: 환경 변수 저장 및 재배포**

1. 모든 환경 변수 입력 완료 후 **Save Changes** 클릭
2. Render가 자동으로 재배포 시작
3. **Deploy 로그** 확인:
   ```
   Build successful
   Starting service
   ```

---

## 🧪 테스트

### **1. 웹 페이지 접속**

https://tshirt-management-web.onrender.com

### **2. 시안 업로드 테스트**

1. **주문 관리** 페이지 접속
2. `CONSULTING` 상태 주문 찾기
3. **시안 업로드** 버튼 클릭
4. 파일 선택 후 **업로드 및 컨펌 완료** 클릭

### **3. 성공 확인**

✅ **성공 메시지:**
```
✅ Google Drive에 시안 파일 X개가 업로드되었습니다!
주문이 제작 중 상태로 변경되었습니다.
마감일: 2025-XX-XX
```

✅ **Google Drive 확인:**
- Google Drive에서 폴더 열기
- `[주문번호]_고객명` 폴더 확인
- 파일이 업로드되어 있는지 확인

---

## 🔍 로그 확인 (문제 발생 시)

### **Render Logs**

1. Render 대시보드 → **Logs** 탭
2. 다음 메시지 확인:
   ```
   OAuth 2.0 방식 사용
   배포 환경: 환경 변수에서 OAuth 토큰 사용
   OAuth 서비스 초기화 성공
   파일 업로드 성공
   ```

### **에러 발생 시**

**에러:** `토큰 갱신 실패 - refresh_token 없음`
**해결:** 새로운 토큰을 생성하여 환경 변수 업데이트

**에러:** `HttpError 403`
**해결:** Google Drive 폴더 권한 확인 (본인 계정으로 생성된 폴더여야 함)

---

## 📌 중요 사항

### **토큰 유효 기간**

- OAuth 토큰은 **자동 갱신**됩니다 (refresh_token 포함)
- 만료 시 자동으로 새로운 access_token 발급
- **주기적으로 확인 불필요**

### **보안**

- 환경 변수에 저장된 토큰은 **Render에서만 접근 가능**
- GitHub에는 **업로드되지 않음** (`.gitignore`에 포함)
- 본인 계정만 사용하므로 안전

### **백업**

토큰 파일을 안전한 곳에 백업하세요:
```bash
cp ~/oauth_tokens/token.pickle ~/oauth_tokens/token.pickle.backup
```

---

## 🎉 완료!

이제 Render에서 OAuth 2.0 방식으로 Google Drive에 파일을 업로드할 수 있습니다!

- ✅ 폴더 생성 성공
- ✅ 파일 업로드 성공
- ✅ 주문 상태 자동 변경
- ✅ 마감일 자동 계산

**Service Account 권한 문제 완전 해결!** 🎊

