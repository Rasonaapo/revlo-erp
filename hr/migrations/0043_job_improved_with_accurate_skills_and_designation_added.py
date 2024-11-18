# Generated by Django 5.1.1 on 2024-11-08 13:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0042_alter_salarygrade_grade_step'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='required_skills',
            field=models.ManyToManyField(related_name='required_for_jobs', to='hr.skill'),
        ),
        migrations.AddField(
            model_name='job',
            name='responsibilities',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='skills',
            field=models.ManyToManyField(blank=True, related_name='employees', to='hr.skill'),
        ),
        migrations.CreateModel(
            name='Designation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=12, null=True, unique=True)),
                ('title', models.CharField(max_length=100, unique=True, verbose_name='Title/Rank')),
                ('level', models.CharField(max_length=100, null=True, verbose_name='Hierarchy Level')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'unique_together': {('title', 'level')},
            },
        ),
    ]
