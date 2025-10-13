"""
고객 ID 관리 유틸리티
"""
import re
from orders.models import Order


def generate_customer_id(customer_name, customer_phone):
    """
    고객명과 연락처를 기반으로 고유한 고객 ID를 생성합니다.
    
    규칙:
    1. 동일한 이름과 연락처가 있으면 이름-001, 이름-002 형식으로 넘버링
    2. 이름만 같고 연락처가 다르면 이름B, 이름C 형식으로 알파벳 추가
    
    Args:
        customer_name (str): 고객명
        customer_phone (str): 연락처
        
    Returns:
        str: 생성된 고객 ID
    """
    # 기존 주문에서 동일한 이름과 연락처를 가진 고객 찾기
    same_name_phone_orders = Order.objects.filter(
        customer_name=customer_name,
        customer_phone=customer_phone
    )
    
    if same_name_phone_orders.exists():
        # 동일한 이름과 연락처가 있으면 숫자 넘버링
        # 기존 주문들의 고객명에서 숫자 패턴 찾기
        max_number = 0
        for order in same_name_phone_orders:
            # 고객명에서 -숫자 패턴 찾기
            match = re.search(r'-(\d+)$', order.customer_name)
            if match:
                number = int(match.group(1))
                max_number = max(max_number, number)
        
        # 다음 번호 생성
        next_number = max_number + 1
        return f"{customer_name}-{next_number:03d}"
    
    # 동일한 이름만 있는 경우 알파벳 추가
    same_name_orders = Order.objects.filter(customer_name=customer_name)
    if same_name_orders.exists():
        # 기존 주문들의 고객명에서 알파벳 패턴 찾기
        used_letters = set()
        for order in same_name_orders:
            # 고객명에서 알파벳 패턴 찾기 (B, C, D 등)
            match = re.search(r'([A-Z])$', order.customer_name)
            if match:
                used_letters.add(match.group(1))
        
        # 사용되지 않은 알파벳 찾기
        for letter in 'BCDEFGHIJKLMNOPQRSTUVWXYZ':
            if letter not in used_letters:
                return f"{customer_name}{letter}"
    
    # 새로운 고객이면 원래 이름 그대로 반환
    return customer_name


def get_customer_orders(customer_name, customer_phone):
    """
    고객의 모든 주문을 조회합니다.
    
    Args:
        customer_name (str): 고객명
        customer_phone (str): 연락처
        
    Returns:
        QuerySet: 고객의 주문 목록
    """
    return Order.objects.filter(
        customer_name=customer_name,
        customer_phone=customer_phone
    ).order_by('-payment_date')


def is_existing_customer(customer_name, customer_phone):
    """
    기존 고객인지 확인합니다.
    
    Args:
        customer_name (str): 고객명
        customer_phone (str): 연락처
        
    Returns:
        bool: 기존 고객 여부
    """
    return Order.objects.filter(
        customer_name=customer_name,
        customer_phone=customer_phone
    ).exists()
