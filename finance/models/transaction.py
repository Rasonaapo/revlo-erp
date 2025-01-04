from django.db import models
from django.core.exceptions import ValidationError
from datetime import timedelta
from decimal import Decimal
from django.utils.translation import gettext_lazy as _

class FinancialYear(models.Model):
    PERIOD_CHOICES = [('3', '3 Months'), ('6', '6 Months'), ('9', '9 Months'), ('12', '12 Months')]
    STATUS_CHOICES = [('open', 'Open'), ('closed', 'Closed')]
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, default='12')
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')

    def __str__(self):
        return f"{self.start_date} to {self.end_date} ({self.get_status_display()})"
    
    def clean(self):
        # Ensure end date is greater than start date
        if self.start_date > self.end_date:
            raise ValidationError(_("End date must be greater than start date"))
        
        # Ensure there is no overlapping financial year
        if FinancialYear.objects.filter(start_date__lte=self.start_date, end_date__gte=self.start_date).exists():
            raise ValidationError(_("Overlapping financial year"))
        
        # Ensure when period is chosen, the start and end date range conform to the peroid, eg 3 months period should have a range of 3 months
        if self.period:
            period = int(self.period)
            period_in_weeks = period * 4
            if self.end_date - self.start_date != timedelta(weeks=period_in_weeks):
                raise ValidationError(_(f"{period} months period should have a range of {period} months"))

        # Ensure only one financial year is open at a time
        if self.status == 'open':
            if FinancialYear.objects.filter(status='open').exclude(id=self.id).exists():
                raise ValidationError(_("Only one financial year can be open at a time"))
            
class TransactionCategory(models.Model):
    LEVEL_CHOICES = [
        ('1', 'Level 1'),
        ('2', 'Level 2'),
        ('3', 'Level 3'),
        ('4', 'Level 4'),
        ('5', 'Level 5'),
    ]
    type = models.CharField(max_length=50)
    detail = models.CharField(max_length=100)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='1')

    def __str__(self):
        return f"{self.type} - {self.detail}"
    
    class Meta:
        verbose_name_plural = 'Transaction Categories'

class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('posted', 'Posted'),
        ('revoked', 'Revoked')
    ]

    date = models.DateField()
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey('TransactionCategory', on_delete=models.PROTECT, related_name='transactions')
    account = models.ForeignKey('finance.Account', on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)
    status = models.CharField(max_length=50)
    reference = models.CharField(max_length=50, unique=True, null=True, blank=True)
    cheque_number = models.CharField(max_length=50, null=True, blank=True)
    # created_by = models.CharField(max_length=50)
    bank = models.ForeignKey('hr.Bank', on_delete=models.PROTECT, related_name='transactions', null=True, blank=True)
    payroll = models.ForeignKey('hr.Payroll', on_delete=models.PROTECT, related_name='transactions', null=True, blank=True)
    loan = models.ForeignKey('hr.Loan', on_delete=models.PROTECT, related_name='transactions', null=True, blank=True)
    sale = models.ForeignKey('sales.Sale', on_delete=models.PROTECT, related_name='transactions', null=True, blank=True)
    purchase_order = models.ForeignKey('operations.PurchaseOrder', on_delete=models.PROTECT, related_name='transactions', null=True, blank=True)
    financial_year = models.ForeignKey('FinancialYear', on_delete=models.PROTECT, related_name='transactions', null=True, blank=True)
    supplier = models.ForeignKey('operations.Supplier', on_delete=models.PROTECT, related_name='transactions', null=True, blank=True)
    customer  = models.ForeignKey('operations.Customer', on_delete=models.PROTECT, related_name='transactions', null=True, blank=True)
    employee = models.ForeignKey('hr.Employee', on_delete=models.PROTECT, related_name='transactions', null=True, blank=True)
    # For suppliers who have not been added to the system
    supplier_name = models.CharField(max_length=100, null=True, blank=True)
    # For customers who have not been added to the system
    customer_name = models.CharField(max_length=100, null=True, blank=True)
    # For employees who have not been added to the system
    employee_name = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.transaction_description

    """ 
    create a method that will return the name of either the supplier from supplier field or purchase_order field
    it should return the name of the either the customer from customer field or sale field
    it should return the name of either the employee from employee field or employee_name field
    else it should return either supplier_name field or customer_name (whatever value is there)
    """   
    def get_client_name(self):
        if self.sale:
            return self.sale.customer
        elif self.purchase_order:
            return self.purchase_order.supplier
        elif self.employee:
            return self.employee
        elif self.customer:
            return self.customer
        elif self.supplier:
            return self.supplier
        elif self.customer_name:
            return self.customer_name
        elif self.supplier_name:
            return self.supplier_name
        elif self.employee_name:
            return self.employee_name
        
    def save(self, *args, **kwargs):
        # Ensure there is at least a financial year opened before committing any transaction
        if not FinancialYear.objects.filter(status='open').exists():
            raise ValidationError(_("There is no active financial year"))
        
        # Ensure the current open financial year is set
        if not self.financial_year:
            self.financial_year = FinancialYear.objects.get(status='open')
        
        # retrieve ledger records of transaction and ensure the sum of credit and debit is equal but convert negative amount into positive on the fly before computing
        if self.status == 'posted':
            credit = sum([ledger.amount for ledger in self.ledgers.filter(entry='credit')])
            debit = sum([ledger.amount for ledger in self.ledgers.filter(entry='debit')])  
            if credit < 0:
                credit = credit * -1
            if debit < 0:
                debit = debit * -1
            if credit != debit:
                raise ValidationError(_("Credit and Debit amount must be equal"))
            
        super().save(*args, **kwargs)


class Ledger(models.Model):
    ENTRY_CHOICES = [
        ('credit', 'Credit'),
        ('debit', 'Debit')
    ]
    transaction = models.ForeignKey('Transaction', on_delete=models.CASCADE, related_name="ledgers")
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    account = models.ForeignKey('finance.Account', on_delete=models.PROTECT, related_name="account_ledgers")
    entry = models.CharField(max_length=10, choices=ENTRY_CHOICES)

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        f"{self.entry} {self.account} - {self.amount}"

    def save(self, *args, **kwargs):
        # Ensure double entry acconting principle
        if self.entry == 'credit':
            if self.account.account_category.category_type in ['asset', 'expense'] and self.amount > 0:
                raise ValidationError(_("Credit entry should be negative for asset and expense accounts"))  
            elif self.account.account_category.category_type in ['liability', 'equity', 'income'] and self.amount < 0:
                raise ValidationError(_("Credit entry should be positive for liability, equity and income accounts"))
        elif self.entry == 'debit':
            if self.account.account_category.category_type in ['asset', 'expense'] and self.amount < 0:
                raise ValidationError(_("Debit entry should be positive for asset and expense accounts"))  
            elif self.account.account_category.category_type in ['liability', 'equity', 'income'] and self.amount > 0:
                raise ValidationError(_("Debit entry should be negative for liability, equity and income accounts"))                
        
        super().save(*args, **kwargs)



