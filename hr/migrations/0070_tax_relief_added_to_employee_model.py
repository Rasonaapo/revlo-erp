# Generated by Django 5.1.1 on 2024-11-23 21:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0069_amount_and_entry_in_payrollitem_modified_to_accept_null'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='tax_relief',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Tax Relief'),
        ),
    ]
