from typing import Any
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.utils.timezone import now
from datetime import timedelta

class SalaryGrade(models.Model):
    CURRENCY_CHOICES = [
        ('USD', 'US Dollars'),
        ('EUR', 'Euros'),
        ('GBP', 'British Pounds'),
        ('GHS', 'Ghanaian Cedi'),
        # We will add more currencies as needed
    ]
    grade = models.CharField(max_length=24 )
    step =  models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(2)])
    grade_step = models.ForeignKey('SalaryStep', null=True, on_delete=models.CASCADE, related_name='salary_grades', verbose_name='Step')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Basic Salary')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='GHS')
     
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('grade', 'step')
        
    def __str__(self):
        return f"{self.grade} - {self.grade_step} - {self.get_currency_symbol()}{self.amount}"

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

class SalaryStep(models.Model):
    step = models.IntegerField(default=1, verbose_name='Salary Step')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.step)
    
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

    @classmethod
    def calculate_tax(cls, year, amount):
        tax = 0
        position = 1
        previous_block = 0

        tax_blocks  = cls.objects.filter(year=year).order_by('rate')
        for item in tax_blocks:
            block = item.block
            rate = item.rate

            if amount > block:
                block_tax = (rate / 100) * block
                tax = tax + block_tax
                if position > 1:
                    amount = amount - previous_block
            else:
                amount = amount - previous_block
                block_tax = (rate / 100) * amount
                tax += block_tax
                break
        
            position += 1
            previous_block = block
        
        return tax

class SalaryItem(models.Model):
    item_name = models.CharField(max_length=100, unique=True, verbose_name='Item Name')
    alias_name = models.CharField(max_length=100, help_text="Name will appear on payslip", verbose_name='Alias Name')
    EFFECT_CHOICES = (
        ('addition', 'Addition'),
        ('deduction', 'Deduction')
    )
    effect = models.CharField(max_length=10, choices=EFFECT_CHOICES, default='addition', verbose_name="Entry")
    RATE_CHOICES = (
        ('fix', 'Fix'),
        ('factor', 'Factor'),
        ('variable', 'Variable')
    )
    rate_type = models.CharField(max_length=10, choices=RATE_CHOICES, default='fix', verbose_name='Rate Type')
    rate_amount = models.DecimalField(max_digits=10, verbose_name="Rate", decimal_places=2)
    rate_dependency = models.CharField(max_length=100, null=True, help_text="Only use when rate is of type 'Variable'", verbose_name="Multiply By Rate")
    STAFF_SOURCE_CHOICES = (
        ('filters', 'Filters'),
        ('import', 'Import')
    )
    staff_source = models.CharField(max_length=8, choices=STAFF_SOURCE_CHOICES, default='filters')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  
    
    # expiry field tells when this item will no longer be inclusive among active list 
    expires_on = models.DateField(null=True, verbose_name='Expires On', help_text="Leave blank if item will continually remain active")
    EMPLOYMENT_TYPE = (
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contractual', 'Contractual'),
        ('temporary', 'Temporary')
    )
    condition = models.CharField(max_length=12, choices=EMPLOYMENT_TYPE, default='full_time')
    step = models.ManyToManyField('SalaryStep', related_name='salary_items', blank=True)
    salary_grade = models.ManyToManyField('SalaryGrade', verbose_name="Salary Grade", related_name="salary_items", blank=True)
    job = models.ManyToManyField('hr.Job', related_name="salary_items", blank=True)
    department = models.ManyToManyField('hr.Department', related_name="salary_items", blank=True)
    designation = models.ManyToManyField('hr.Designation', related_name="salary_items", blank=True)
    applicable_to = models.ManyToManyField('hr.Employee', verbose_name="Applicable To", related_name='applicable_salary_items', blank=True)
    excluded_from = models.ManyToManyField('hr.Employee', verbose_name="Excluded From",  related_name='excluded_salary_items', blank=True)
    eligible_employee_count = models.PositiveIntegerField(default=0, editable=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.skip_update_signal = False  # Flag to prevent recursion

    def __str__(self):
        return f"{self.item_name}"
    
    def display_salary_item_step(self):
        return ",".join(step.step for step in self.step.all())
   
    def display_salary_item_job(self):
        return ",".join(job.job_title for job in self.job.all())

    def display_salary_item_grade(self):
        return ",".join(grade.grade for grade in self.salary_grade.all())

    def display_salary_item_department(self):
        return ",".join(dept.department_name for dept in self.department.all())

    def display_salary_item_designation(self):
        return ",".join(desg.title for desg in self.designation.all())

    def display_salary_item_applicable_to(self):
        return ",".join(f"{emp.first_name} {emp.last_name}" for emp in self.applicable_to.all())

    def display_salary_item_excluded_from(self):
        return ",".join(f"{emp.first_name} {emp.last_name}" for emp in self.excluded_from.all())

    def get_eligible_employees(self):
        """
        Returns a queryset of eligible employees based on the specified filters.
        If `applicable_to` is set, returns only those employees.
        Otherwise, filters by `step`, `salary_grade`, `job`, `department`, and `designation`
        and excludes any employees listed in `excluded_from`.
        """
        from hr.models.employee import Employee

        # If `applicable_to` is set, return those employees directly
        if self.applicable_to.exists():
            return self.applicable_to.all()

        # Start with all employees
        eligible_employees = Employee.objects.active()

        # Apply hierarchical filters if set
        if self.step.exists():
            eligible_employees = eligible_employees.filter(salary_grade__step__in=self.step.all())
        if self.salary_grade.exists():
            eligible_employees = eligible_employees.filter(salary_grade__in=self.salary_grade.all())
        if self.job.exists():
            eligible_employees = eligible_employees.filter(job__in=self.job.all())
        if self.department.exists():
            eligible_employees = eligible_employees.filter(job__department__in=self.department.all())
        if self.designation.exists():
            eligible_employees = eligible_employees.filter(designation__in=self.designation.all())

        # Filter by employment type if `condition` is specified
        if self.condition:
            eligible_employees = eligible_employees.filter(employment_type=self.condition)

        # Exclude employees listed in `excluded_from`
        if self.excluded_from.exists():
            eligible_employees = eligible_employees.exclude(id__in=self.excluded_from.values_list('id', flat=True))

        return eligible_employees   

    def update_eligible_employee_count(self):
        """
        Updates the `eligible_employee_count` field with the current count of eligible employees.
        """
        self.eligible_employee_count = self.get_eligible_employees().count()
        self.save(update_fields=['eligible_employee_count'])

class StaffSalaryItem(models.Model):
    salary_item = models.ForeignKey('SalaryItem', on_delete=models.CASCADE, verbose_name="Salary Item", related_name="staff_salary_items")
    employee = models.ForeignKey('hr.Employee', on_delete=models.CASCADE)
    variable = models.IntegerField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  

    class Meta:
        unique_together = ('salary_item', 'employee')
    
    def __str__(self):
        return f"{self.employee} on {self.salary_item} @ {self.amount}"

class Loan(models.Model):
    class LoanStatus(models.TextChoices):
        PENDING = 'pending', 'Pending Approval'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        ACTIVE = 'active', 'Active'
        PAID_OFF = 'paid_off', 'Paid Off'
        DEFAULTED = 'defaulted', 'Defaulted'

    class LoanType(models.TextChoices):
        SALARY_ADVANCE = 'salary_advance', 'Salary Advance'
        RENT_ADVANCE = 'rent_advance', 'Rent Advance'
        VEHICLE = 'vehicle', 'Vehicle Loan'
        PERSONAL = 'personal', 'Personal Loan'
        MEDICAL = 'medical', 'Medical Loan'
        EDUCATION = 'education', 'Education Loan'

    employee = models.ForeignKey('hr.Employee', on_delete=models.CASCADE, related_name='loans')
    loan_type = models.CharField(max_length=20, choices=LoanType.choices, default=LoanType.SALARY_ADVANCE, verbose_name="Loan Type")  # Example: "Housing Loan", "Car Loan"
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Principal Amount")
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name="Interest Rate (%)")
    duration_in_months = models.PositiveIntegerField(verbose_name="Duration (Months)")
    monthly_installment = models.DecimalField(max_digits=12, decimal_places=2, editable=False, verbose_name="Monthly Installment")
    total_repayable_amount = models.DecimalField(max_digits=12, decimal_places=2, editable=False, verbose_name="Total Repayable Amount")
    outstanding_balance = models.DecimalField(max_digits=12, decimal_places=2, editable=False, verbose_name="Outstanding Balance", default=Decimal('0.00'))
    status = models.CharField(max_length=10, choices=LoanStatus.choices, default=LoanStatus.PENDING, verbose_name="Loan Status")
    purpose = models.TextField(null=True, blank=True, verbose_name="Loan Purpose")
    applied_on = models.DateField(auto_now_add=True, verbose_name="Applied On")
    approved_on = models.DateField(null=True, blank=True, verbose_name="Approved On")
    deduction_end_date = models.DateField(null=True, blank=True, verbose_name="Deduction End Date")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  

    def clean(self):
        super().clean()
        if self.loan_type == self.LoanType.SALARY_ADVANCE and self.interest_rate != 0.00:
            raise ValidationError("Salary Advances must have an interest rate of 0.00%")

    def __str__(self):
        return f"{self.loan_type} - {self.employee.first_name} {self.employee.last_name} ({self.status})"

    def calculate_installments(self):
        """
        Calculate monthly installment and total repayable amount.
        Uses a simple interest formula: A = P(1 + rt).
        """
        # Simple interest calculation: A = P(1 + rt), where t = repayment_period_months / 12
        if self.interest_rate == 0.00:
            return self.principal_amount / self.duration_in_months
        total_amount = self.principal_amount * (1 + (self.interest_rate / 100))
        return total_amount / self.duration_in_months


    def update_status(self):
        """
        Automatically updates the loan status based on conditions.
        """
        if self.status == self.LoanStatus.APPROVED and self.outstanding_balance > 0:
            self.status = self.LoanStatus.ACTIVE

        if self.deduction_end_date and now().date() > self.deduction_end_date and self.outstanding_balance > 0:
            self.status = self.LoanStatus.DEFAULTED

        if self.outstanding_balance <= 0:
            self.status = self.LoanStatus.PAID_OFF

    def save(self, *args, **kwargs):
        # Calculate monthly installments and total repayable amount
        self.monthly_installment = self.calculate_installments()

        # Auto set approved_on and deduction_end_date when status is approved
        if self.status == self.LoanStatus.APPROVED and not self.approved_on:
            self.approved_on = now().date()
            self.deduction_end_date = self.approved_on + timedelta(days=30 * self.duration_in_months)

        # Clear approved_on and deduction_end_date if status changes back to non-approved
        elif self.status != self.LoanStatus.APPROVED:
            self.approved_on = None
            self.deduction_end_date = None

        # Update loan status
        self.update_status()

        # Ensure outstanding_balance is initialized for new loans
        if not self.pk:  # New Loan
            self.outstanding_balance = self.total_repayable_amount

        super().save(*args, **kwargs)



class LoanRepayment(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayments')
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Amount Paid")
    date_paid = models.DateField(default=now, verbose_name="Date Paid")
    payment_reference = models.CharField(max_length=100, null=True, blank=True, verbose_name="Payment Reference")

    def save(self, *args, **kwargs):
        # Update loan's outstanding balance
        self.loan.outstanding_balance -= self.amount_paid
        # Update loan's status
        self.loan.update_status()
        self.loan.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Repayment of {self.amount_paid} for Loan #{self.loan.id} on {self.date_paid}"
