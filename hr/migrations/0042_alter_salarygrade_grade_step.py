# Generated by Django 5.1.1 on 2024-11-08 00:01

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0041_grade_step_related_name_changed_to_salary_grades'),
    ]

    operations = [
        migrations.AlterField(
            model_name='salarygrade',
            name='grade_step',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='salary_grades', to='hr.salarystep', verbose_name='Step'),
        ),
    ]
