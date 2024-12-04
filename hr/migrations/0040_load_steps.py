# Generated by Django 5.1.1 on 2024-11-07 23:30

from django.db import migrations


class Migration(migrations.Migration):

    def load_steps(apps, schema_editor):
        SalaryStep = apps.get_model('hr', 'SalaryStep')
        entries = []
        for i in range(1, 10):
            entries.append(SalaryStep(step=i))
        SalaryStep.objects.bulk_create(entries)

    dependencies = [
        ('hr', '0039_salary_item_and_salary_step_added'),
    ]

    operations = [
        migrations.RunPython(load_steps)
    ]