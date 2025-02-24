# Generated by Django 5.1.1 on 2025-01-28 18:01

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('operations', '0007_verbose_names_added_to_deliveryroute'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductUnit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('barcode', models.CharField(max_length=255, null=True, unique=True)),
                ('quantity_per_unit', models.PositiveIntegerField(help_text='Number of smaller units in this unit type', verbose_name='Quantity Per Unit')),
                ('cost_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('sale_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('is_purchasable', models.BooleanField(default=True, help_text='Can be purchased from supplier')),
                ('is_sellable', models.BooleanField(default=True, help_text='Can be sold to customers')),
            ],
        ),
        migrations.CreateModel(
            name='UnitType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.RemoveIndex(
            model_name='inventory',
            name='operations__product_632b14_idx',
        ),
        migrations.RemoveField(
            model_name='product',
            name='barcode',
        ),
        migrations.RemoveField(
            model_name='product',
            name='cost_price',
        ),
        migrations.RemoveField(
            model_name='product',
            name='sale_price',
        ),
        migrations.RemoveField(
            model_name='product',
            name='variant',
        ),
        migrations.AddField(
            model_name='product',
            name='is_composite',
            field=models.BooleanField(default=False, help_text='Whether product can be broken down into smaller units'),
        ),
        migrations.AddField(
            model_name='productunit',
            name='parent_unit',
            field=models.ForeignKey(blank=True, help_text='Next larger unit type', null=True, on_delete=django.db.models.deletion.PROTECT, to='operations.productunit'),
        ),
        migrations.AddField(
            model_name='productunit',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='units', to='operations.product'),
        ),
        migrations.AlterUniqueTogether(
            name='inventory',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='inventory',
            name='product_unit',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, related_name='inventories', to='operations.productunit', verbose_name='Product Unit'),
        ),
        migrations.AlterUniqueTogether(
            name='inventory',
            unique_together={('warehouse', 'product_unit')},
        ),
        migrations.AddIndex(
            model_name='inventory',
            index=models.Index(fields=['product_unit'], name='operations__product_903ec9_idx'),
        ),
        migrations.AddIndex(
            model_name='inventory',
            index=models.Index(fields=['warehouse', 'product_unit'], name='operations__warehou_9ea85d_idx'),
        ),
        migrations.AddField(
            model_name='productunit',
            name='unit_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='product_units', to='operations.unittype', verbose_name='Unit Type'),
        ),
        migrations.RemoveField(
            model_name='inventory',
            name='product',
        ),
        migrations.AlterUniqueTogether(
            name='productunit',
            unique_together={('product', 'unit_type')},
        ),
    ]
