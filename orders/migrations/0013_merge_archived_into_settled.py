from django.db import migrations, models


def merge_archived_into_settled(apps, schema_editor):
    Order = apps.get_model("orders", "Order")
    Order.objects.filter(status="ARCHIVED").update(status="SETTLED")


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0012_add_performance_indexes"),
    ]

    operations = [
        migrations.RunPython(merge_archived_into_settled, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("NEW", "등록"),
                    ("CONSULTING", "결제"),
                    ("PRODUCING", "옷주문"),
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
