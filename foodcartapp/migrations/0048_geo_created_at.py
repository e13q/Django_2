# Generated by Django 3.2.15 on 2024-11-16 03:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0047_auto_20241116_0519'),
    ]

    operations = [
        migrations.AddField(
            model_name='geo',
            name='created_at',
            field=models.DateTimeField(auto_now=True, db_index=True, verbose_name='время фиксации'),
        ),
    ]
