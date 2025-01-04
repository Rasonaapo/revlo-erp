from django.db import models
from hr.models.payroll import Bank

class AccountCategory(models.Model):
    TYPE_CHOICES = [
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('expense', 'Expense'),
        ('income', 'Income'),
        ('equity', 'Equity')
    ]

    DETAIL_CHOICES = [
        # Asset class
        ('cash_equivalent', 'Cash Equivalent'),
        ('account_receivable', 'Account Receivable'),
        ('current_asset', 'Current Asset'),
        ('non_current_asset', 'Non-Current Asset'),
        ('fixed_asset', 'Fixed Asset'),
        # Liability class    
        ('current_liability', 'Current Liability'),
        ('account_payable', 'Account Payable'),
        ('non_current_liability', 'Non-Current Liability'),
        # Equity class
        ('equity', 'Owners Equity'),
        # Income class
        ('income', 'Income'),
        ('other_income', 'Other Income'),
        # Expense class
        ('expense', 'Expense'),
        ('cost_of_goods_sold', 'Cost of Goods Sold'),
        ('operating_expense', 'Operating Expense'),
        ('depreciation', 'Depreciation'),
        ('amortization', 'Amortization'),
        ('other_expense', 'Other Expense'),
    ]

    category_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Account Type")
    category_detail = models.CharField(max_length=30,  choices=DETAIL_CHOICES, verbose_name="Account Detail")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.category_type} - {self.get_category_detail_display()}"
    
    class Meta:
        verbose_name_plural = 'Account Categories'

    
class Account(models.Model):
    account_name = models.CharField(max_length=100, unique=True, verbose_name="Account Name")
    account_number = models.CharField(max_length=100, unique=True, verbose_name='Account Code/Number', help_text="Not to be confused with bank a/c number")
    account_category = models.ForeignKey('AccountCategory', related_name="accounts", on_delete=models.PROTECT, verbose_name="Account Detail")
    parent_account = models.ForeignKey('self', null=True, blank=True, related_name='sub_accounts', on_delete=models.SET_NULL, verbose_name="Parent Account")
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    bank = models.ForeignKey(Bank, null=True, blank=True, related_name='bank_accounts', on_delete=models.SET_NULL)
    active = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False, verbose_name="System Account", help_text="System accounts cannot be deleted")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['account_name']),
            models.Index(fields=['account_number']),
            models.Index(fields=['account_category']),
            models.Index(fields=['parent_account']),
        ]

    def __str__(self):
        if self.parent_account:
            return f"{self.parent_account.account_name} -> {self.account_name}"
        return self.account_name
