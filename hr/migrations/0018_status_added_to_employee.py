# Generated by Django 5.1.1 on 2024-10-16 15:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0017_department_removed_from_employee_job_assigned'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='status',
            field=models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive'), ('on_leave', 'On Leave'), ('terminated', 'Terminated'), ('probation', 'Probation'), ('retired', 'Retired'), ('resigned', 'Resigned')], default='active', max_length=10),
        ),
    ]