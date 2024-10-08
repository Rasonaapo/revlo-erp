# Generated by Django 5.1.1 on 2024-10-05 16:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0005_bank_added_and_employee_more_additions_employeeid_bank_etc'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bank',
            name='bank_name',
            field=models.CharField(max_length=254, unique=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='branch',
            field=models.CharField(max_length=254, null=True, verbose_name='Branch'),
        ),
    ]
