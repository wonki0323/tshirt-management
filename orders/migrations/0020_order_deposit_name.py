from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0019_order_clothing_post_processing_discount'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='deposit_name',
            field=models.CharField(
                blank=True,
                default='',
                help_text='송금 시 사용할 입금자명. 뱅크다 자동매치 기준 (정확 일치 필수). 비워두면 자동매치 미작동·운영자 수동 처리',
                max_length=50,
                verbose_name='입금자명',
            ),
        ),
    ]
