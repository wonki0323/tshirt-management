from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0016_add_archived_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='print_method',
        ),
    ]
