# Generated by Django 5.1.1 on 2024-10-21 20:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0027_load_public_holidays'),
    ]

    operations = [
        migrations.AlterField(
            model_name='publicholiday',
            name='name',
            field=models.CharField(max_length=255, unique=True),
        ),
    ]
