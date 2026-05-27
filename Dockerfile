# syntax=docker/dockerfile:1.6
# Django 티셔츠 관리 시스템 — 컨테이너 이미지
# 본 이전 단계 1 (로컬 Docker) → 단계 2~7 (naxer-main) 동일 이미지 사용

FROM python:3.9.6-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=tshirt_management.settings

WORKDIR /app

# psycopg2-binary는 wheel로 옴(빌드 도구 불요). pillow는 wheel 제공.
# libpq5만 런타임 의존(psycopg2-binary 내부에 동봉되긴 하지만 명시).
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip \
 && pip install -r requirements.txt

COPY . .

# collectstatic은 SECRET_KEY 더미값으로 빌드 단계에서 실행 (Render buildCommand와 동일 패턴).
# 실제 SECRET_KEY는 런타임 환경변수로 주입.
RUN SECRET_KEY=build-time-dummy-key DEBUG=False \
    python manage.py collectstatic --noinput

EXPOSE 8000

# 비-루트 사용자
RUN useradd --create-home --uid 1000 app \
 && chown -R app:app /app
USER app

CMD ["gunicorn", "tshirt_management.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
