# Generated by Django 5.1.1 on 2025-01-04 17:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0010_format_transaction_categories_to_title_case'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='accountcategory',
            options={'verbose_name_plural': 'Account Categories'},
        ),
        migrations.AlterModelOptions(
            name='transactioncategory',
            options={'verbose_name_plural': 'Transaction Categories'},
        ),
        migrations.AddField(
            model_name='account',
            name='is_system',
            field=models.BooleanField(default=False, help_text='System accounts cannot be deleted', verbose_name='System Account'),
        ),
    ]
