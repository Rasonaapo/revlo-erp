# Generated by Django 5.1.1 on 2024-12-09 13:58

import django.db.models.deletion
import django_quill.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administration', '0001_meeting_model_relocated'),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Category Name')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Vendor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Vendor Name')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='Email Address')),
                ('phone_number', models.CharField(max_length=15, blank=True, null=True, unique=True, verbose_name='Phone Number')),
                ('address', models.CharField(max_length=255, null=True)),
                ('notes', django_quill.fields.QuillField(blank=True, null=True, verbose_name='Notes')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='BusinessDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('document_name', models.CharField(max_length=255, verbose_name='Document Name')),
                ('associated_entity', models.CharField(blank=True, max_length=255, null=True, verbose_name='Associated Entity')),
                ('document_file', models.FileField(upload_to='business_documents/', verbose_name='File')),
                ('expiration_date', models.DateField(blank=True, null=True, verbose_name='Expiration Date')),
                ('notes', django_quill.fields.QuillField(blank=True, null=True, verbose_name='Notes')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='administration.documentcategory', verbose_name='Category')),
                ('vendor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='documents', to='administration.vendor', verbose_name='Vendor')),
            ],
            options={
                'verbose_name': 'Business Document',
                'verbose_name_plural': 'Business Documents',
            },
        ),
    ]
