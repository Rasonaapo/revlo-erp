# Generated by Django 5.1.1 on 2024-11-18 15:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0058_loan_models_created'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loan',
            name='applied_on',
            field=models.DateField(verbose_name='Applied On'),
        ),
    ]
