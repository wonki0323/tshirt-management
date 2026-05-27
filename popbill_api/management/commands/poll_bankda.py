"""뱅크다 폴링 cron — systemd timer로 30분 주기 호출."""
from django.core.management.base import BaseCommand

from popbill_api.services import sync_bankda_deposits


class Command(BaseCommand):
    help = '뱅크다 REST API로 신규 입금 내역 동기화 + 자동매칭'

    def handle(self, *args, **options):
        result = sync_bankda_deposits()
        if result.get('error'):
            self.stderr.write(self.style.ERROR(f"error={result['error']}"))
            return
        self.stdout.write(
            self.style.SUCCESS(
                f"new={result['new']} matched={result['matched']}"
            )
        )
