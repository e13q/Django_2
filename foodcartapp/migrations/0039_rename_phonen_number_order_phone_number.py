# Generated by Django 3.2.15 on 2024-11-09 18:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0038_order_orderproduct'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='phonen_number',
            new_name='phone_number',
        ),
    ]
