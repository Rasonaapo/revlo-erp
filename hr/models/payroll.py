from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class SalaryGrade(models.Model):
    CURRENCY_CHOICES = [
        ('USD', 'US Dollars'),
        ('EUR', 'Euros'),
        ('GBP', 'British Pounds'),
        ('GHS', 'Ghanaian Cedi'),
        # We will add more currencies as needed
    ]
    grade = models.CharField(max_length=24 )
    step = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(2)])
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Basic Salary')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='GHS')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('grade', 'step')
        
    def __str__(self):
        return f"{self.grade} - {self.step} - {self.get_currency_symbol()}{self.amount}"

    def get_currency_symbol(self):
        """Return the symbol for the currency"""
        symbols = {
            'USD': '$',   # US Dollar
            'EUR': '€',   # Euro
            'GBP': '£',   # British Pound
            'GHS': '₵',   # Ghanaian Cedi
            # We will add more currency symbols as needed
        }
        return symbols.get(self.currency, self.currency)  # Default to currency code if symbol not found

class Bank(models.Model):
    bank_name = models.CharField(max_length=254, unique=True)
    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.bank_name
    

class Tax(models.Model):
    year = models.PositiveIntegerField()  
    block = models.FloatField(null=True, blank=True)  
    rate = models.FloatField(null=True, blank=True)
    active = models.BooleanField(default=True)  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  

    class Meta:
        verbose_name_plural = 'Taxes'  # makes the admin plural nicer

    def __str__(self):
        return f"Tax for year {self.year} - Block: {self.block}, Rate: {self.rate}"

