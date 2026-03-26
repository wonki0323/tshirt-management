from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0007_product_is_physical'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='item_type',
            field=models.CharField(choices=[('PRODUCT', '제품'), ('POST_PROCESSING', '후가공')], default='PRODUCT', help_text='제품 또는 후가공 항목을 선택하세요', max_length=20, verbose_name='항목 유형'),
        ),
        migrations.AddField(
            model_name='product',
            name='product_group',
            field=models.CharField(blank=True, default='반팔', help_text='예: 반팔, 긴팔, 스웻셔츠, 기타', max_length=50, verbose_name='제품 그룹'),
        ),
    ]
