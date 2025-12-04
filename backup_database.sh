#!/bin/bash

# Render PostgreSQL 데이터베이스 백업 스크립트
# 사용법: ./backup_database.sh

# 기존 DATABASE_URL을 여기에 입력 (Render Dashboard에서 복사)
OLD_DATABASE_URL="postgresql://user:password@host/dbname"

# 백업 파일명
BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"

echo "📦 데이터베이스 백업 시작..."

# pg_dump를 사용하여 백업
pg_dump "$OLD_DATABASE_URL" > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "✅ 백업 완료: $BACKUP_FILE"
    echo ""
    echo "복원 방법:"
    echo "psql \$NEW_DATABASE_URL < $BACKUP_FILE"
else
    echo "❌ 백업 실패"
    exit 1
fi

