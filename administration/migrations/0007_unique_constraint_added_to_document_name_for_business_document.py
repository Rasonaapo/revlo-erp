# Generated by Django 5.1.1 on 2024-12-10 14:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administration', '0006_related_name_for_business_document_file_now_documentfiles'),
    ]

    operations = [
        migrations.AlterField(
            model_name='businessdocument',
            name='document_name',
            field=models.CharField(max_length=255, unique=True, verbose_name='Document Name'),
        ),
    ]
