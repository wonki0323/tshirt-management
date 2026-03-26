"""
테스트용 더미 데이터 생성 관리 명령어
"""
import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from orders.models import Order, OrderItem, Status
from products.models import Product, ProductOption


class Command(BaseCommand):
    help = '기존 데이터를 삭제하고 테스트용 더미 데이터 20개를 생성합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=20,
            help='생성할 주문 개수 (기본값: 20)'
        )

    def handle(self, *args, **options):
        count = options['count']
        
        self.stdout.write(self.style.WARNING('⚠️  기존 데이터 삭제 중...'))
        
        # 기존 데이터 삭제
        deleted_items = OrderItem.objects.all().delete()
        deleted_orders = Order.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS(f'✅ 주문 항목 {deleted_items[0]}개 삭제 완료'))
        self.stdout.write(self.style.SUCCESS(f'✅ 주문 {deleted_orders[0]}개 삭제 완료'))
        
        # 제품 옵션 확인
        product_options = list(ProductOption.objects.all())
        if not product_options:
            self.stdout.write(self.style.ERROR('❌ 제품 옵션이 없습니다. 먼저 제품을 생성해주세요.'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'✅ {len(product_options)}개의 제품 옵션 발견'))
        
        # 테스트용 고객 이름
        customer_names = [
            '김철수', '이영희', '박민수', '최지영', '정우진',
            '강서연', '조민호', '윤지혜', '임태양', '한소희',
            '송민재', '배수지', '오정석', '신예은', '문재인',
            '장동건', '김태희', '이병헌', '전지현', '현빈',
            '손예진', '박서준', '김수현', '이민호', '배용준'
        ]
        
        # 주문 상태 분포 (다양한 상태로 생성)
        status_distribution = [
            Status.NEW,
            Status.NEW,
            Status.NEW,
            Status.CONSULTING,
            Status.CONSULTING,
            Status.CONSULTING,
            Status.CONSULTING,
            Status.PRODUCED,
            Status.PRODUCED,
            Status.COMPLETED,
            Status.COMPLETED,
            Status.SETTLED,
            Status.ARCHIVED,
        ]
        
        self.stdout.write(self.style.WARNING(f'🔄 {count}개의 테스트 주문 생성 중...'))
        
        created_orders = []
        
        for i in range(count):
            # 랜덤 고객 정보
            customer_name = random.choice(customer_names)
            customer_phone = f'010-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}'
            
            # 랜덤 날짜 (최근 30일 내)
            days_ago = random.randint(0, 30)
            payment_date = timezone.now() - timedelta(days=days_ago)
            
            # 랜덤 주소
            districts = ['강남구', '서초구', '송파구', '강동구', '마포구', '용산구', '영등포구', '관악구']
            address = f'서울시 {random.choice(districts)} {random.choice(["테헤란로", "강남대로", "논현로", "선릉로"])} {random.randint(1, 200)}'
            
            # 랜덤 상태
            status = random.choice(status_distribution)
            
            # 주문 생성
            order = Order.objects.create(
                smartstore_order_id=f'SS{2025000000 + i + 1:06d}',
                status=status,
                payment_date=payment_date,
                customer_name=customer_name,
                customer_phone=customer_phone,
                shipping_address=address,
                total_order_amount=Decimal('0')  # 나중에 업데이트
            )
            
            # 상태에 따라 추가 필드 설정
            if status in [
                Status.PRODUCED,
                Status.COMPLETED,
                Status.SETTLED,
                Status.ARCHIVED,
            ]:
                order.confirmed_date = payment_date + timedelta(days=random.randint(1, 3))
                order.due_date = (order.confirmed_date + timedelta(days=3)).date()
                order.google_drive_folder_url = f'https://drive.google.com/drive/folders/dummy_{order.id}'
            if status in [Status.COMPLETED, Status.SETTLED, Status.ARCHIVED]:
                order.shipping_date = (payment_date + timedelta(days=random.randint(4, 10))).date()
                order.tracking_number = f'{random.randint(100000000000, 999999999999)}'
            
            order.save()
            
            # 랜덤으로 1~3개의 주문 항목 생성
            num_items = random.randint(1, 3)
            total_amount = Decimal('0')
            
            for j in range(num_items):
                product_option = random.choice(product_options)
                quantity = random.randint(1, 5)
                
                # 가격 설정 (제품 옵션의 가격 또는 랜덤)
                unit_price = product_option.price if hasattr(product_option, 'price') else Decimal(str(random.randint(15000, 50000)))
                unit_cost = product_option.base_cost
                
                OrderItem.objects.create(
                    order=order,
                    product_option=product_option,
                    smartstore_product_name=product_option.product.name,
                    smartstore_option_text=product_option.option_detail,
                    quantity=quantity,
                    unit_price=unit_price,
                    unit_cost=unit_cost
                )
                
                total_amount += unit_price * quantity
            
            # 주문 총액 업데이트
            order.total_order_amount = total_amount
            order.save()
            
            created_orders.append(order)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'  ✅ [{i+1}/{count}] {order.smartstore_order_id} - '
                    f'{order.customer_name} ({order.get_status_display()}) - '
                    f'{total_amount:,}원 ({num_items}개 항목)'
                )
            )
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS(f'🎉 테스트 데이터 생성 완료!'))
        self.stdout.write(self.style.SUCCESS(f'   총 {count}개의 주문이 생성되었습니다.'))
        self.stdout.write('')
        
        # 상태별 통계
        self.stdout.write(self.style.WARNING('📊 상태별 통계:'))
        for status, label in Status.choices:
            count_by_status = Order.objects.filter(status=status).count()
            if count_by_status > 0:
                self.stdout.write(f'   - {label}: {count_by_status}개')
        
        self.stdout.write(self.style.SUCCESS('=' * 70))
