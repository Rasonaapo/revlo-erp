# Generated by Django 5.1.1 on 2024-11-25 14:29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0073_process_month_changed_to_choices_and_error_mode_added_in_payroll'),
    ]

    operations = [
        migrations.CreateModel(
            name='PayrollError',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('error_category', models.CharField(choices=[('bank', 'Missing Bank Details'), ('salary_grade', 'Missing Salary Grade')], max_length=12)),
                ('error_details', models.TextField(help_text='Details of the missing or invalid data.', null=True, verbose_name='Error Details')),
                ('resolved', models.BooleanField(default=False, verbose_name='Is Resolved?')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Error Logged At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Last Updated At')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payroll_errors', to='hr.employee', verbose_name='Employee')),
                ('payroll', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='errors', to='hr.payroll', verbose_name='Related Payroll')),
            ],
            options={
                'verbose_name': 'Payroll Error',
                'verbose_name_plural': 'Payroll Errors',
                'ordering': ['-created_at'],
            },
        ),
    ]