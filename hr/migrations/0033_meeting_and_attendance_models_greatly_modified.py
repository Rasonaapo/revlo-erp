# Generated by Django 5.1.1 on 2024-10-31 23:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0032_skill_model_many_to_many_to_employee'),
    ]

    operations = [
        migrations.AddField(
            model_name='meeting',
            name='department',
            field=models.ManyToManyField(related_name='meetings', to='hr.department'),
        ),
        migrations.AddField(
            model_name='meeting',
            name='job',
            field=models.ManyToManyField(related_name='meetings', to='hr.job'),
        ),
        migrations.AddField(
            model_name='meeting',
            name='salary_grade',
            field=models.ManyToManyField(related_name='meetings', to='hr.salarygrade', verbose_name='Salary Grade'),
        ),
        migrations.AddField(
            model_name='meeting',
            name='sms',
            field=models.TextField(help_text='Note: SMS will prepend staff ID and append meeting date & venue', null=True),
        ),
        migrations.AlterField(
            model_name='attendance',
            name='check_in_time',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='meeting',
            name='agenda',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='meeting',
            name='location',
            field=models.CharField(max_length=100, verbose_name='Venue'),
        ),
        migrations.AlterField(
            model_name='meeting',
            name='meeting_date',
            field=models.DateTimeField(verbose_name='Meeting Date'),
        ),
        migrations.AlterField(
            model_name='meeting',
            name='sms_date',
            field=models.DateTimeField(verbose_name='SMS Date & Time'),
        ),
    ]
