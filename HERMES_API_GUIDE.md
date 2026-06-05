# HERMES → ERP 읽기 게이트웨이 안내서

> hermes 에이전트가 아키노 ERP(`data.naxer.shop`) 자료를 **읽기 전용**으로 조회하는 방법.
> 작성 2026-06-06. Phase 1 = 읽기 전용. 쓰기(생성/수정/삭제)는 정기 백업 체계 확립 후 별도 개통 예정.

---

## 1. 인증

- **엔드포인트**: `POST https://data.naxer.shop/hermes/query/`
- **헤더**: `X-Hermes-Key: <발급받은 키>`  (이 키는 hermes 쪽 `.env`의 `HERMES_API_KEY`에 보관)
- 키 누락/불일치 → `401`

> ⚠️ 키는 비밀. 로그·코드·외부 전송 컨텍스트에 노출 금지.

---

## 2. 요청 형식

```jsonc
{
  "model":   "orders.Order",          // 필수. "app_label.Model" 형식
  "filters": {"status": "PRODUCED"},  // 선택. Django filter kwargs (AND 결합)
  "exclude": {"is_urgent": true},     // 선택. Django exclude kwargs
  "fields":  ["id", "customer_name", "status"],  // 선택. 생략 시 전체 필드
  "order_by":["-created_at"],          // 선택. "-"는 내림차순
  "limit":   100,                      // 선택. 기본 100, 상한 500
  "offset":  0                         // 선택. 페이지네이션
}
```

**필터 lookup** (Django 문법 그대로):
- `{"status": "PAID"}` — 일치
- `{"customer_name__icontains": "김"}` — 부분일치(대소문자 무시)
- `{"total_order_amount__gte": 50000}` — 이상
- `{"created_at__date": "2026-06-01"}` — 날짜
- `{"status__in": ["PAID", "PRODUCED"]}` — 여러 값

## 3. 응답 형식

```jsonc
{
  "success": true,
  "model": "orders.Order",
  "count": 3,        // 이번 응답 행 수
  "total": 13,       // 필터 적용 후 전체 행 수 (페이지네이션 기준)
  "limit": 100, "offset": 0,
  "results": [ { ...행... }, ... ]
}
```
- 실패: `{"success": false, "error": "..."}` + 상태코드(400/401/403)
- 잘못된 필드명으로 400이 나면 `error`에 **사용 가능한 필드 목록**이 들어옴 → 그걸 보고 교정

---

## 4. 조회 가능한 모델 (15개)

| 모델 (model 값) | 내용 |
|---|---|
| `products.Product` | 상품 |
| `products.ProductOption` | 상품 옵션 |
| `orders.Order` | **주문** (핵심) |
| `orders.OrderItem` | 주문 품목 |
| `orders.OrderThumbnail` | 주문 시안 썸네일 |
| `orders.OrderCompletionPhoto` | 제작 완료 사진 |
| `orders.AddressExtractionRequest` | 주소 자동등록 요청 큐 |
| `orders.ShipNotifyRequest` | 발송 통보 요청 큐 |
| `orders.KakaoConsultCard` | 카톡 상담 카드(칸반) |
| `orders.KakaoOpenRequest` | 카톡창 열기 요청 큐 |
| `finance.Expense` | 지출 |
| `finance.Purchase` | 매입 |
| `popbill_api.Deposit` | 입금(뱅크다) |
| `popbill_api.CashReceipt` | 현금영수증 |

**차단된 모델** (조회 시 403): `settings_app.APISettings`(자격증명), Django 내장 `auth.*`·`sessions.*`·`admin.*`·`contenttypes.*`(비밀번호 해시·세션키 등).

### `orders.Order` 주요 필드 (참고)
`id`, `customer_name`, `customer_phone`, `status`, `total_order_amount`, `shipping_address`, `tracking_number`, `due_date`, `payment_date`, `shipping_date`, `confirmed_date`, `is_urgent`, `is_on_hold`, `customer_memo`, `kakao_customer_id`, `smartstore_order_id`, `created_at`, `updated_at`
- 관계 필드(`items`, `thumbnails`, `deposits`, `kakao_cards` 등)는 별도 모델로 따로 조회 (filters에 `order_id`로 묶기)
- **필드를 모르면**: `fields` 생략하고 `limit:1`로 한 건 받아서 키 목록 확인

---

## 5. 호출 예시 (Python)

```python
import requests, os

BASE = "https://data.naxer.shop/hermes/query/"
HEADERS = {"X-Hermes-Key": os.environ["HERMES_API_KEY"]}

def query(model, **opts):
    body = {"model": model, **opts}
    r = requests.post(BASE, json=body, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not data.get("success"):
        raise RuntimeError(data.get("error"))
    return data["results"]

# 제작중인 주문
orders = query("orders.Order", filters={"status": "PRODUCED"},
               fields=["id", "customer_name", "due_date"], order_by=["due_date"])

# 특정 주문의 품목
items = query("orders.OrderItem", filters={"order_id": 27})

# 이번 달 입금
deposits = query("popbill_api.Deposit", filters={"created_at__date": "2026-06-06"})
```

---

## 6. 제약 / 주의

- **읽기 전용**: 생성·수정·삭제 경로는 서버 코드에 아예 없음. 쓰기 시도해도 불가.
- 한 호출 **최대 500행** (`limit` 상한). 더 필요하면 `offset`으로 페이지네이션.
- 응답에 고객 개인정보(이름·전화·주소)가 포함됨 → hermes가 이를 외부로 전송·로깅하지 않도록 주의.
- 게이트웨이 코드: ERP `tshirt_management/hermes_views.py`. URL `tshirt_management/urls.py`.
