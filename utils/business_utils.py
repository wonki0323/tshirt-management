"""
비즈니스 로직 유틸리티 함수들
"""
import numpy as np
from datetime import datetime, date, timedelta
from django.utils import timezone


def calculate_business_days(start_date, days_to_add):
    """
    시작일로부터 지정된 영업일 수를 더한 날짜를 계산합니다.
    주말(토/일)은 제외하고 계산합니다.
    
    Args:
        start_date: 시작 날짜 (datetime 또는 date 객체)
        days_to_add: 더할 영업일 수 (int)
    
    Returns:
        datetime: 계산된 날짜
    """
    if isinstance(start_date, datetime):
        start_date = start_date.date()
    
    # 주말인 경우 다음 월요일로 이동
    if start_date.weekday() >= 5:  # 토요일(5) 또는 일요일(6)
        days_until_monday = 7 - start_date.weekday()
        start_date = start_date + timedelta(days=days_until_monday)
    
    # numpy의 busday_offset을 사용하여 영업일 계산
    # 주말(토/일)만 제외 (weekmask='1111100' = 월~금만)
    try:
        result_date = np.busday_offset(start_date, days_to_add, weekmask='1111100')
    except ValueError:
        # 주말인 경우 다음 영업일부터 시작
        result_date = np.busday_offset(start_date, days_to_add, weekmask='1111100', roll='forward')
    
    # numpy의 datetime64를 Python date로 변환
    if isinstance(result_date, np.datetime64):
        # numpy datetime64 -> datetime -> date
        result_date = np.datetime64(result_date, 'D').astype('datetime64[D]')
        result_date = result_date.astype('O')  # numpy datetime64 to datetime.date
    
    # date 객체가 아닌 경우 처리
    if not isinstance(result_date, date):
        result_date = date.fromisoformat(str(result_date))
    
    # timezone-aware datetime으로 변환
    return timezone.make_aware(datetime.combine(result_date, datetime.min.time()))


def get_next_business_day(start_date, days=1):
    """
    시작일로부터 다음 영업일을 계산합니다.
    
    Args:
        start_date: 시작 날짜
        days: 더할 영업일 수 (기본값: 1)
    
    Returns:
        datetime: 다음 영업일
    """
    return calculate_business_days(start_date, days)
