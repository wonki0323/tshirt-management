from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0015_remove_producing_status"),
    ]

    operations = [
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
                    ("ARCHIVED", "정산 목록"),
                    ("CANCELED", "주문 취소"),
                ],
                default="NEW",
                max_length=20,
                verbose_name="주문 상태",
            ),
        ),
    ]
