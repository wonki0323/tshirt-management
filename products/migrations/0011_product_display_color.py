from django.db import migrations, models


def copy_option_color_to_product(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    ProductOption = apps.get_model('products', 'ProductOption')
    for product in Product.objects.all():
        first_colored = ProductOption.objects.filter(product=product).exclude(option_color='').first()
        if first_colored and first_colored.option_color:
            product.display_color = first_colored.option_color
            product.save(update_fields=['display_color'])


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0010_set_post_processing_group_blank'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='display_color',
            field=models.CharField(default='#B0BEC5', help_text='후가공 표시 박스에 사용할 색상', max_length=20, verbose_name='표시 박스색'),
        ),
        migrations.RunPython(copy_option_color_to_product, migrations.RunPython.noop),
    ]
