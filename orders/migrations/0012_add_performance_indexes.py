# Generated migration for performance optimization

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0011_order_shipping_date_alter_order_customer_phone'),
    ]

    operations = [
        # Order 모델 인덱스 추가
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['status', '-payment_date'], name='orders_stat_paym_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['due_date'], name='orders_due_date_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['customer_name'], name='orders_cust_name_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['payment_date'], name='orders_payment_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['updated_at'], name='orders_updated_idx'),
        ),
    ]

