# Generated by Django 5.1.1 on 2024-11-30 06:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0083_indexes_added_to_models'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='payrollitem',
            name='amount_idx',
        ),
        migrations.AddIndex(
            model_name='payrollitem',
            index=models.Index(fields=['payroll', 'dependency'], name='payroll_dependency_idx'),
        ),
        migrations.AddIndex(
            model_name='payrollitem',
            index=models.Index(fields=['payroll', 'entry'], name='payroll_entry_idx'),
        ),
    ]