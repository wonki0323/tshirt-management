from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = '관리자 계정 생성'

    def handle(self, *args, **options):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin1234'  # 로그인 후 반드시 변경하세요!
            )
            self.stdout.write(self.style.SUCCESS('✅ 관리자 계정 생성 완료'))
            self.stdout.write(self.style.WARNING('Username: admin'))
            self.stdout.write(self.style.WARNING('Password: admin1234'))
            self.stdout.write(self.style.ERROR('⚠️  보안을 위해 로그인 후 비밀번호를 변경하세요!'))
        else:
            self.stdout.write(self.style.WARNING('관리자 계정이 이미 존재합니다.'))





