# Generated by Django 5.1.1 on 2024-11-23 02:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0067_m2m_fields_rename_in_singular'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payroll',
            name='step',
            field=models.ManyToManyField(blank=True, related_name='payroll', to='hr.salarystep', verbose_name='Steps'),
        ),
    ]