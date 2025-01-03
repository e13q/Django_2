# Generated by Django 3.2.15 on 2024-11-16 02:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0046_order_restaurant'),
    ]

    operations = [
        migrations.CreateModel(
            name='Geo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lat', models.DecimalField(decimal_places=6, max_digits=9, verbose_name='широта')),
                ('lon', models.DecimalField(decimal_places=6, max_digits=9, verbose_name='долгота')),
            ],
            options={
                'verbose_name': 'геопозиция',
                'verbose_name_plural': 'геопозиции',
            },
        ),
        migrations.AddField(
            model_name='order',
            name='coordinates',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='foodcartapp.geo', verbose_name='геопозиция'),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='coordinates',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='foodcartapp.geo', verbose_name='геопозиция'),
        ),
    ]
