"""hermes 에이전트 읽기 전용 게이트웨이 (read-only ORM query gateway).

설계: WEB_AGENT 세션 2026-06-06 — hermes(WSL LLM 에이전트)가 ERP 자료를
HTTP API로 조회. 다른 컴퓨터(로컬 WSL)라 DB 직접 접근 불가 → ktalk와 동일하게
API 키 인증 경유. Phase 1 = 읽기 전용. 쓰기는 정기 백업 체계 확립 후 별도.

- 인증: 헤더 X-Hermes-Key == 환경변수 HERMES_API_KEY (ktalk 패턴 복제)
- 전체 모델 동적 조회 (apps.get_model). 쓰기/생성/수정/삭제 함수 자체가 없음 = 구조적 read-only.
- 차단:
  * settings_app.APISettings  — 뱅크다·팝빌·카톡 등 자격증명 보관 (원칙 12)
  * auth / sessions / admin / contenttypes — 비밀번호 해시·세션키 등 침해 위험. 비즈니스 자료 아님
"""
import json
import os

from django.apps import apps
from django.core.exceptions import FieldError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

# 앱 단위 차단 — Django 내장 인증/세션/관리 테이블 (비번 해시·세션키 = 계정 침해 위험)
DENY_APPS = {"auth", "sessions", "admin", "contenttypes"}
# 모델 단위 차단 — 자격증명 보관 (app_label.model, 소문자)
DENY_MODELS = {"settings_app.apisettings"}
# 한 호출 최대 행 수 — 과다 조회/덤프 방지
MAX_LIMIT = 500


def _check_hermes_api_key(request):
    """hermes 전용 endpoint 인증. 헤더 X-Hermes-Key 검증 (ktalk 패턴 동일)."""
    expected = os.environ.get("HERMES_API_KEY", "")
    provided = request.headers.get("X-Hermes-Key", "")
    return bool(expected) and provided == expected


@csrf_exempt
@require_http_methods(["POST"])
def hermes_query(request):
    """[hermes] 읽기 전용 ORM 게이트웨이.

    body 예시:
      {
        "model": "orders.Order",          # app_label.Model (필수)
        "filters": {"status": "PRODUCED"}, # Django filter kwargs (선택)
        "exclude": {"is_urgent": true},    # Django exclude kwargs (선택)
        "fields": ["id", "customer_name", "status"],  # 생략 시 전체 필드 (선택)
        "order_by": ["-created_at"],       # (선택)
        "limit": 100,                      # 상한 500
        "offset": 0
      }
    응답: {"success", "model", "count", "total", "limit", "offset", "results": [...]}
    """
    if not _check_hermes_api_key(request):
        return JsonResponse({"success": False, "error": "인증 실패"}, status=401)

    try:
        data = json.loads(request.body or b"{}")
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({"success": False, "error": "JSON 파싱 실패"}, status=400)
    if not isinstance(data, dict):
        return JsonResponse({"success": False, "error": "body는 JSON 객체여야 함"}, status=400)

    model_label = (data.get("model") or "").strip()
    if not model_label:
        return JsonResponse({"success": False, "error": "model 필수 (예: orders.Order)"}, status=400)

    # 차단 검사
    if "." not in model_label:
        return JsonResponse(
            {"success": False, "error": "model은 app_label.Model 형식 (예: orders.Order)"}, status=400
        )
    app_label, model_name = model_label.split(".", 1)
    if app_label.lower() in DENY_APPS or model_label.lower() in DENY_MODELS:
        return JsonResponse({"success": False, "error": f"{model_label}: 조회 차단된 모델"}, status=403)

    try:
        model = apps.get_model(app_label, model_name)
    except (ValueError, LookupError):
        return JsonResponse({"success": False, "error": f"모델 없음: {model_label}"}, status=400)

    filters = data.get("filters") or {}
    exclude = data.get("exclude") or {}
    fields = data.get("fields") or []
    order_by = data.get("order_by") or []
    if not all(isinstance(x, dict) for x in (filters, exclude)):
        return JsonResponse({"success": False, "error": "filters/exclude는 객체여야 함"}, status=400)

    try:
        limit = int(data.get("limit", 100))
        offset = int(data.get("offset", 0))
    except (TypeError, ValueError):
        return JsonResponse({"success": False, "error": "limit/offset은 정수여야 함"}, status=400)
    limit = max(1, min(limit, MAX_LIMIT))
    offset = max(0, offset)

    try:
        qs = model.objects.all()
        if filters:
            qs = qs.filter(**filters)
        if exclude:
            qs = qs.exclude(**exclude)
        if order_by:
            qs = qs.order_by(*order_by)
        total = qs.count()
        qs = qs.values(*fields) if fields else qs.values()
        results = list(qs[offset : offset + limit])
    except FieldError as e:
        return JsonResponse({"success": False, "error": f"필드 오류: {e}"}, status=400)
    except Exception as e:  # 잘못된 lookup 값 등
        return JsonResponse({"success": False, "error": f"조회 실패: {type(e).__name__}: {e}"}, status=400)

    return JsonResponse(
        {
            "success": True,
            "model": model_label,
            "count": len(results),
            "total": total,
            "limit": limit,
            "offset": offset,
            "results": results,
        },
        json_dumps_params={"ensure_ascii": False},  # 한글 보존
    )
