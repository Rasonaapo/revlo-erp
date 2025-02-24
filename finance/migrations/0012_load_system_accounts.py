# Generated by Django 5.1.1 on 2025-01-04 17:35

from django.db import migrations


class Migration(migrations.Migration):
    def load_default_system_accounts(apps, schema_editor):
        Account = apps.get_model('finance', 'Account')
        AccountCategory = apps.get_model('finance', 'AccountCategory')
        
        system_accounts = [
            # Asset Accounts
            {
                'account_name': 'Undeposited Funds',
                'account_number': '1001',
                'category_type': 'asset',
                'category_detail': 'cash_equivalent'
            },
            {
                'account_name': 'Opening Balance Bank',
                'account_number': '1002',
                'category_type': 'asset',
                'category_detail': 'cash_equivalent'
            },
            {
                'account_name': 'Opening Balance Accounts Receivable',
                'account_number': '1100',
                'category_type': 'asset',
                'category_detail': 'account_receivable'
            },
            
            # Liability Accounts
            {
                'account_name': 'Opening Balance Accounts Payable',
                'account_number': '2000',
                'category_type': 'liability',
                'category_detail': 'account_payable'
            },
            {
                'account_name': 'Suspense Account',
                'account_number': '2100',
                'category_type': 'liability',
                'category_detail': 'current_liability'
            },
            {
                'account_name': 'Sales Tax Payable',
                'account_number': '2200',
                'category_type': 'liability',
                'category_detail': 'current_liability'
            },
            
            # Equity Accounts
            {
                'account_name': 'Opening Balance Equity',
                'account_number': '3000',
                'category_type': 'equity',
                'category_detail': 'equity'
            },
            {
                'account_name': 'Retained Earnings',
                'account_number': '3100',
                'category_type': 'equity',
                'category_detail': 'equity'
            },
            
            # Income Accounts
            {
                'account_name': 'Opening Balance Income',
                'account_number': '4000',
                'category_type': 'income',
                'category_detail': 'income'
            },
            {
                'account_name': 'Other Income',
                'account_number': '4100',
                'category_type': 'income',
                'category_detail': 'other_income'
            },
            {
                'account_name': 'Bank Interest Earned',
                'account_number': '4101',
                'category_type': 'income',
                'category_detail': 'other_income'
            },      
            # Expense Accounts
            {
                'account_name': 'Opening Balance Expense',
                'account_number': '5000',
                'category_type': 'expense',
                'category_detail': 'expense'
            },
            {
                'account_name': 'Bank Service Charges',
                'account_number': '5100',
                'category_type': 'expense',
                'category_detail': 'operating_expense'
            },
            {
                'account_name': 'Exchange Gain or Loss',
                'account_number': '5200',
                'category_type': 'expense',
                'category_detail': 'other_expense'
            }
        ]
        
        for account in system_accounts:
            category = AccountCategory.objects.get(
                category_type=account['category_type'],
                category_detail=account['category_detail']
            )
            Account.objects.get_or_create(
                account_name=account['account_name'],
                account_number=account['account_number'],
                account_category=category,
                balance=0,
                active=True,
                is_system=True,
            )

    dependencies = [
        ('finance', '0011_is_system_added_to_account_model'),
    ]

    operations = [
       migrations.RunPython(
          load_default_system_accounts,
          migrations.RunPython.noop
        ),
    ]
