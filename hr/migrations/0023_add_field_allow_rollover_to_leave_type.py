# Generated by Django 5.1.1 on 2024-10-17 22:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0022_load_employees_load_balances'),
    ]

    operations = [
        migrations.AddField(
            model_name='leavetype',
            name='allow_rollover',
            field=models.BooleanField(default=False, verbose_name='Allow Rollover'),
        ),
    ]