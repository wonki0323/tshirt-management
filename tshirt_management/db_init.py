"""
SQLite 성능 최적화 설정
"""
from django.db.backends.signals import connection_created
from django.dispatch import receiver


@receiver(connection_created)
def setup_sqlite_pragmas(sender, connection, **kwargs):
    """SQLite 연결 시 PRAGMA 설정으로 성능 최적화"""
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        # Write-Ahead Logging 모드로 성능 향상
        cursor.execute('PRAGMA journal_mode=WAL;')
        # 동기화 레벨 낮춰서 쓰기 성능 향상
        cursor.execute('PRAGMA synchronous=NORMAL;')
        # 캐시 크기를 64MB로 증가
        cursor.execute('PRAGMA cache_size=-64000;')
        # 임시 테이블을 메모리에 저장
        cursor.execute('PRAGMA temp_store=MEMORY;')
        # 외래 키 제약 조건 활성화
        cursor.execute('PRAGMA foreign_keys=ON;')
        cursor.close()

