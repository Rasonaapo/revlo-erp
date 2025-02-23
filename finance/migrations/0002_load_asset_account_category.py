# Generated by Django 5.1.1 on 2024-12-22 22:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0001_initial'),
    ]
    def load_asset_account_categories(apps, schema_editor):
        AccountCategory = apps.get_model('finance', 'AccountCategory')
        categories = [
            # Asset class
            {'type': 'asset', 'category': 'cash_equivalent'},
            {'type': 'asset', 'category': 'account_receivable'},
            {'type': 'asset', 'category': 'current_asset'},
            {'type': 'asset', 'category': 'non_current_asset'},
            {'type': 'asset', 'category': 'fixed_asset'},
        ]
       
        for category in categories:
            AccountCategory.objects.create(category_type=category['type'], category_detail=category['category'])
   
    operations = [
        migrations.RunPython(load_asset_account_categories),
    ]
