from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0020_order_deposit_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='is_on_hold',
            field=models.BooleanField(
                default=False,
                help_text='컨트롤 패널 칸반에서 보류 칸으로 드래그된 주문. 해제 시 원래 status 유지',
                verbose_name='보류',
            ),
        ),
    ]
