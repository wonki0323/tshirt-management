from django.db import migrations


def set_post_processing_group_blank(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    Product.objects.filter(item_type='POST_PROCESSING').update(product_group='')


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0009_productoption_option_color_and_defaults'),
    ]

    operations = [
        migrations.RunPython(set_post_processing_group_blank, migrations.RunPython.noop),
    ]
