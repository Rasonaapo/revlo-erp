# Generated by Django 5.1.1 on 2024-11-04 07:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0035_status_default_altered'),
    ]

    operations = [
        migrations.CreateModel(
            name='SMS',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField(help_text='Note: SMS will prepend staff ID', null=True)),
                ('sms_date', models.DateTimeField(verbose_name='SMS Date & Time')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('dispatched', 'Dispatched')], default='pending', max_length=10)),
                ('department', models.ManyToManyField(related_name='sms', to='hr.department')),
                ('salary_grade', models.ManyToManyField(related_name='sms', to='hr.salarygrade', verbose_name='Salary Grade')),
            ],
        ),
    ]