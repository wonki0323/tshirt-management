"""
정산목록(SETTLED) 주문을 종료목록(ARCHIVED)으로 일괄 이동하는 커맨드

사용법:
    python manage.py move_settled_to_archived
"""

from django.core.management.base import BaseCommand
from orders.models import Order, Status


class Command(BaseCommand):
    help = '정산목록(SETTLED) 주문을 종료목록(ARCHIVED)으로 일괄 이동'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제로 변경하지 않고 결과만 미리보기',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # SETTLED 상태의 모든 주문 조회
        settled_orders = Order.objects.filter(status=Status.SETTLED)
        count = settled_orders.count()
        
        if count == 0:
            self.stdout.write(
                self.style.WARNING('정산목록에 주문이 없습니다.')
            )
            return
        
        self.stdout.write(f'\n총 {count}개의 주문을 찾았습니다.\n')
        
        # 주문 목록 출력
        for order in settled_orders:
            self.stdout.write(
                f'  - [{order.smartstore_order_id}] {order.customer_name} '
                f'(결제일: {order.payment_date.strftime("%Y-%m-%d")}, '
                f'금액: {order.total_order_amount:,.0f}원)'
            )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\n[DRY RUN] 위 {count}개 주문이 종료목록으로 이동됩니다.'
                )
            )
            self.stdout.write(
                self.style.NOTICE(
                    '\n실제로 변경하려면 --dry-run 옵션 없이 실행하세요.'
                )
            )
        else:
            # 실제 변경
            updated = settled_orders.update(status=Status.ARCHIVED)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ {updated}개의 주문이 종료목록(ARCHIVED)으로 이동되었습니다.'
                )
            )

