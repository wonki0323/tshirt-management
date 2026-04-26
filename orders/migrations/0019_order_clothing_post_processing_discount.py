import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0018_add_order_is_urgent"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="clothing_discount_percent",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="0~100%. 제품(의류) 줄 합계에 적용됩니다.",
                max_digits=5,
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(100),
                ],
                verbose_name="의류(제품) 할인율",
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="post_processing_discount_percent",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="0~100%. 후가공 줄 합계에 적용됩니다.",
                max_digits=5,
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(100),
                ],
                verbose_name="후가공 할인율",
            ),
        ),
    ]
