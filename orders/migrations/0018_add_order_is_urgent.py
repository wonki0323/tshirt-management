from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0017_remove_print_method'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='is_urgent',
            field=models.BooleanField(default=False, help_text='긴급 처리 대상 주문 여부', verbose_name='긴급 주문'),
        ),
    ]
