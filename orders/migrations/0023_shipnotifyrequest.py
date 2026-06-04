from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0022_addressextractionrequest'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShipNotifyRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('PENDING', '대기'), ('PROCESSING', '처리중'), ('COMPLETED', '완료'), ('FAILED', '실패')], default='PENDING', max_length=20, verbose_name='요청 상태')),
                ('kakao_chat_name', models.CharField(max_length=100, verbose_name='카톡 대화명 (요청 시점 스냅샷)')),
                ('tracking_number', models.CharField(max_length=100, verbose_name='송장번호 (요청 시점 스냅샷)')),
                ('photo_urls_json', models.TextField(blank=True, default='[]', help_text='ktalk이 다운로드해 발송할 완료사진 URL들', verbose_name='완료사진 URL 리스트 JSON')),
                ('error', models.TextField(blank=True, default='', verbose_name='오류 메시지')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='생성일시')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='수정일시')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ship_notify_requests', to='orders.order', verbose_name='주문')),
            ],
            options={
                'verbose_name': '발송결과 통보 요청',
                'verbose_name_plural': '발송결과 통보 요청',
                'ordering': ['-created_at'],
            },
        ),
    ]
