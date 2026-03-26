from django.db import migrations, models


def merge_producing_into_produced(apps, schema_editor):
    Order = apps.get_model("orders", "Order")
    Order.objects.filter(status="PRODUCING").update(status="PRODUCED")


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0014_remove_order_orders_stat_paym_idx_and_more"),
    ]

    operations = [
        migrations.RunPython(merge_producing_into_produced, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("NEW", "등록"),
                    ("CONSULTING", "결제"),
                    ("PRODUCED", "제작중"),
                    ("COMPLETED", "발송"),
                    ("SETTLED", "결과통보"),
                    ("CANCELED", "주문 취소"),
                ],
                default="NEW",
                max_length=20,
                verbose_name="주문 상태",
            ),
        ),
    ]
