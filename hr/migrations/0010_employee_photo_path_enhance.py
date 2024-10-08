# Generated by Django 5.1.1 on 2024-10-08 02:43

import hr.models.employee
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0009_currency_added_to_salary_grade'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='photo',
            field=models.ImageField(default='avatar.png', null=True, upload_to=hr.models.employee.employee_photo_upload_path),
        ),
    ]