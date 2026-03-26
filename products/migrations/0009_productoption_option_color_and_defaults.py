from django.db import migrations, models


def set_item_type_defaults(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    Product.objects.filter(item_type='POST_PROCESSING').update(is_active=True)
    Product.objects.filter(item_type='POST_PROCESSING').update(product_group='')
    Product.objects.filter(item_type='PRODUCT').update(is_physical=True)


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0008_product_item_type_product_group'),
    ]

    operations = [
        migrations.AddField(
            model_name='productoption',
            name='option_color',
            field=models.CharField(blank=True, default='', help_text='후가공 선택 시 사용할 색상', max_length=50, verbose_name='색상'),
        ),
        migrations.RunPython(set_item_type_defaults, migrations.RunPython.noop),
    ]
