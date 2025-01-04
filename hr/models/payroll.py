from typing import Any
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from datetime import timedelta, date
from django.db import transaction
from decimal import Decimal
from django.db.models import Index

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
        indexes = [
            Index(fields=['year'], name='tax_year_idx'),
            Index(fields=['rate'], name='tax_rate_idx'),
            Index(fields=['block'], name='tax_block_idx'),
        ]


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
    outstanding_balance = models.DecimalField(max_digits=12, decimal_places=2, editable=True, verbose_name="Outstanding Balance", default=Decimal('0.00'))
    status = models.CharField(max_length=10, choices=LoanStatus.choices, default=LoanStatus.PENDING, verbose_name="Loan Status")
    purpose = models.TextField(null=True, blank=True, verbose_name="Loan Purpose")
    applied_on = models.DateField(verbose_name="Applied On")
    approved_on = models.DateField(null=True, blank=True, verbose_name="Approved On")
    active_on = models.DateField(null=True, blank=True, verbose_name='Active On')
    deduction_end_date = models.DateField(null=True, blank=True, verbose_name="Deduction End Date")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            Index(fields=['loan_type', 'status'], name='loantype_status_idx'),
            Index(fields=['loan_type'], name='loan_type_idx'),
            Index(fields=['employee', 'status'], name='loan_status_idx'),
            Index(fields=['active_on'], name='active_on_idx'),
            Index(fields=['deduction_end_date'], name='loan_end_date_idx'),
        ]  

    def clean(self):
        super().clean()
        if self.loan_type == self.LoanType.SALARY_ADVANCE and self.interest_rate != 0.00:
            raise ValidationError("Salary Advances must have an interest rate of 0.00%")

    def __str__(self):
        return f"{self.get_loan_type_display()} - {self.employee.first_name} {self.employee.last_name} ({self.get_status_display()})"

    # Create series of themes based on status of loan
    def get_status_theme(self):
            theme = 'info'
            status = self.status 

            if status == 'active': 
                theme = 'success'
            elif status == 'rejected':
                theme = 'dark'
            elif status == 'approved':
                theme = 'warning'
            elif status == 'paid_off':
                theme = 'primary'
            # elif status == 'pending':
            #     theme = 'info'
            elif status == 'defaulted':
                theme = 'danger label-table'
            
            return theme
            

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

    def update_outstanding_balance(self, amount_paid):
        self.outstanding_balance -= amount_paid
        
    def update_status(self):
        """
        Automatically updates the loan status based on conditions.
        """
        # if self.status == self.LoanStatus.APPROVED and self.outstanding_balance > 0:
        #     self.status = self.LoanStatus.ACTIVE
        # status will be set to Active when PV is finally created and paid to staff

        if self.deduction_end_date and now().date() > self.deduction_end_date and self.outstanding_balance > 0:
            self.status = self.LoanStatus.DEFAULTED

        if self.outstanding_balance <= 0:
            self.status = self.LoanStatus.PAID_OFF

    def save(self, recalculate_balance = True,  *args, **kwargs):
        # Calculate monthly installments and total repayable amount
        self.monthly_installment = self.calculate_installments()

        # Ensure outstanding_balance is initialized for new loans and recaculated only if explicitly allowed else where
        self.total_repayable_amount = self.monthly_installment * self.duration_in_months

        if recalculate_balance:
            self.outstanding_balance = self.total_repayable_amount

        # Auto set active and deduction_end_date when status is active by posting PV in finance system
        if self.status == self.LoanStatus.ACTIVE and not self.active_on:
            active_on = now().date()
            self.deduction_end_date = active_on + timedelta(days=30 * self.duration_in_months)
            self.active_on = active_on

        # Clear approved_on and deduction_end_date if status changes back to non-approved
        if self.status == self.LoanStatus.APPROVED and not self.approved_on:
            self.approved_on = now().date()

        elif self.status != self.LoanStatus.APPROVED and (self.status != self.LoanStatus.ACTIVE):
            self.approved_on = None

        # Update loan status
        self.update_status()

        super().save(*args, **kwargs)


class LoanRepayment(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayments')
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Amount Paid")
    date_paid = models.DateField(default=now, verbose_name="Date Paid")
    payment_reference = models.CharField(max_length=100, null=True, blank=True, verbose_name="Payment Reference")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 

    def save(self, *args, **kwargs):
        from decimal import Decimal

        # Update outstanding balance
        repayment_amount = Decimal(self.amount_paid)
        self.loan.outstanding_balance = Decimal(self.loan.outstanding_balance) - repayment_amount

        # Prevent negative balances
        if self.loan.outstanding_balance < 0:
            self.loan.outstanding_balance = Decimal('0.00')

        # Update loan status (e.g., PAID_OFF, DEFAULTED) if necessary
        self.loan.update_status()

        # Save the loan without recalculating the outstanding_balance
        self.loan.save(recalculate_balance=False)  # Prevents resetting the balance during repayment

        # Save repayment
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Repayment of {self.amount_paid} for Loan #{self.loan.id} on {self.date_paid}"

class CreditUnion(models.Model):
    union_name = models.CharField(max_length=150, unique=True, verbose_name="Credit Union Description", help_text="Union can be welfare group, bank etc")
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Amount (Default)", help_text="If entered, will be the default for all staff in this union, leave it blank for varying amount")
    all_employee = models.BooleanField(default=False, verbose_name="Include All Staff")
    department = models.ManyToManyField('hr.Department', related_name="credit_unions", blank=True)
    applicable_to = models.ManyToManyField('hr.Employee', verbose_name="Applicable To", related_name='applicable_credit_unions', blank=True)
    excluded_from = models.ManyToManyField('hr.Employee', related_name="excluded_credit_unions", verbose_name="Excluded From", blank=True)
    deduction_start_date = models.DateField(null=True, blank=True, verbose_name="Deduction Start Date", help_text="Default date where deduction will commmence for all employees")
    deduction_end_date = models.DateField(null=True, blank=True, verbose_name="Deduction End Date", help_text="When omitted, deduction will continue indefinitely")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 

    def __str__(self):
        return self.union_name
    
    def display_credit_union_department(self):
        return ",".join([department.department_name  for department in self.department.all()])

    def display_credit_union_applicable_to(self):
        return ",".join([f"{employee.first_name} {employee.last_name}"  for employee in self.applicable_to.all()])

    def display_credit_union_excluded_from(self):
        return ",".join([f"{employee.first_name} {employee.last_name}"  for employee in self.excluded_from.all()])
  

    def clean(self):
        super().clean()

        # Ensure that start date and end date aren't the same if only they're supplied
        if self.deduction_start_date and self.deduction_end_date:
            if self.deduction_start_date >= self.deduction_end_date:
                raise ValidationError("Start date must be earlier than the end date")
        elif self.deduction_end_date and not self.deduction_start_date: 
            # raise error for situation where end date is supplied without start date
                raise ValidationError("Start date must be set if an end date is specified.")
        # elif self.deduction_start_date and self.deduction_start_date < date.today():
        #     raise ValidationError("Start date can not be in the past")

    def get_eligible_employees(self):
        from hr.models.employee import Employee
        # Get all active employee when all_employee is checked
        eligiblie_employees = Employee.objects.active()
       
       # if all_employee is checked, return all but exclude staff that may be excluded
        if self.all_employee:
            if self.excluded_from.exists():
                eligiblie_employees = eligiblie_employees.exclude(id__in=self.excluded_from.values_list('id', flat=True))
            return eligiblie_employees
        
        # Apply other filters 
        if self.applicable_to.exists():
            eligiblie_employees = self.applicable_to.all()
        if self.department.exists():
            eligiblie_employees = eligiblie_employees.filter(job__department__in=self.department.all())
        if self.excluded_from.exists():
            eligiblie_employees = eligiblie_employees.exclude(id__in=self.excluded_from.values_list('id', flat=True))
        
        return eligiblie_employees



class StaffCreditUnion(models.Model):
    employee = models.ForeignKey('hr.Employee', on_delete=models.CASCADE, related_name='staff_credit_unions')
    credit_union = models.ForeignKey('CreditUnion', on_delete=models.CASCADE, verbose_name='Credit Union', related_name="staff_credit_unions")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monthly Deduction")
    deduction_start_date = models.DateField(null=True, blank=True, verbose_name="Deduction Start Date", help_text="Until date is entered, deduction won't take place")
    deduction_end_date = models.DateField(null=True, blank=True, verbose_name="Deduction Start Date", help_text="When omitted, deduction will continue indefinitely.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 

    class Meta:
        indexes = [
            Index(fields=['deduction_start_date'], name='cu_deduction_start_idx'),
            Index(fields=['deduction_end_date'], name='cu_deduction_end_idx'),
            Index(fields=['employee'], name='cu_employee_idx'),
            Index(fields=['credit_union'], name='cu_union_idx'),
        ]

    def __str__(self):
        return f"{self.employee} - {self.credit_union}"

    def clean(self):
        super().clean()
        if self.amount < 0:
            raise ValidationError("The deduction amount must be greater than 0.")
        if self.deduction_start_date and self.deduction_end_date:
            if self.deduction_start_date >= self.deduction_end_date:
                raise ValidationError("Deduction start date must be earlier than the end date.")

class StaffCreditUnionDeduction(models.Model):
    staff_credit_union = models.ForeignKey('StaffCreditUnion', on_delete=models.CASCADE, verbose_name="Staff Credit Union", related_name="staff_credit_unions")
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    date_paid = models.DateField(default=now, verbose_name="Date Paid")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  

    def __str__(self):
        return f"{self.staff_credit_union} - {self.amount_paid}"

# Payroll 

class Payroll(models.Model):
    PAYROLL_MONTH = (
    ('01', 'January'),
    ('02', 'February'),
    ('03', 'March'),
    ('04', 'April'),
    ('05', 'May'),
    ('06', 'June'),
    ('07', 'July'),
    ('08', 'August'),
    ('09', 'September'),
    ('10', 'October'),
    ('11', 'November'),
    ('12', 'December'),
    )

    process_month = models.CharField(max_length=12, choices=PAYROLL_MONTH, verbose_name="Processing Month")  # 1 to 12
    process_year = models.PositiveIntegerField(verbose_name="Processing Year")
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name="Payroll Description")
    active = models.BooleanField(default=True, verbose_name="Is Active")
    posted = models.BooleanField(default=False, verbose_name="Is Posted")
    salary_grade = models.ManyToManyField('hr.SalaryGrade', blank=True, related_name="payrolls", verbose_name="Salary Grades")
    department = models.ManyToManyField('hr.Department', blank=True, related_name="payrolls", verbose_name="Departments")
    designation = models.ManyToManyField('hr.Designation', blank=True, related_name="payrolls", verbose_name="Designations")
    step = models.ManyToManyField(SalaryStep, blank=True, related_name="payroll", verbose_name="Steps")
    applicable_to = models.ManyToManyField('hr.Employee', blank=True, related_name="applicable_payrolls", verbose_name="Applicable To")
    excluded_from = models.ManyToManyField('hr.Employee', blank=True, related_name="excluded_payrolls", verbose_name="Excluded From")
    EMPLOYMENT_TYPE = (
        ('all', 'All Types'),
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contractual', 'Contractual'),
        ('temporary', 'Temporary')
    )
    condition = models.CharField(max_length=12, choices=EMPLOYMENT_TYPE, default='all', verbose_name="Employment Type")
    ERROR_MODE = (
        ('strict', 'Strict mode ensures all staff records are accurate and complete before processing'),
        ('mute', 'Mute/Silence mode processes payroll to the exclusion of staff with incomplete records')
    )
    error_mode = models.CharField(max_length=12, choices=ERROR_MODE, default='strict', verbose_name="Error Processing Mode")
    payment_rate = models.IntegerField(verbose_name="Payment Rate", default=100, validators=[MinValueValidator(1), MaxValueValidator(100)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    pv_count = models.IntegerField(verbose_name="Number of Vouchers", default=0, editable=False)

    class Meta:
        verbose_name_plural = "Payrolls"
        unique_together = ('process_month', 'process_year', 'payment_rate', 'description',   'condition')
        indexes = [
            Index(fields=['process_month', 'process_year'], name='month_year_idx'),
            Index(fields=['active'], name='active_idx'),
            Index(fields=['posted'], name='posted_idx'),
        ]

    def __str__(self):
        return f"Payroll {self.process_month}/{self.process_year}"

    def display_payroll_step(self):
        return ",".join(step.step for step in self.step.all())
   
    def display_payroll_grade(self):
        return ",".join(grade.grade for grade in self.salary_grade.all())

    def display_payroll_department(self):
        return ",".join(dept.department_name for dept in self.department.all())

    def display_payroll_designation(self):
        return ",".join(desg.title for desg in self.designation.all())

    def display_payroll_applicable_to(self):
        return ",".join(f"{emp.first_name} {emp.last_name}" for emp in self.applicable_to.all())

    def display_payroll_excluded_from(self):
        return ",".join(f"{emp.first_name} {emp.last_name}" for emp in self.excluded_from.all())

    def get_eligible_employees(self):
        from hr.models.employee import Employee

        employees = Employee.objects.active()

        # First apply the condition filter
        if self.condition != 'all':
            employees = employees.filter(employment_type=self.condition)

        # Apply remaining filters

        if self.applicable_to.exists():
            employees = employees.filter(id__in=self.applicable_to.values_list("id", flat=True))
        if self.excluded_from.exists():
            employees = employees.exclude(id__in=self.excluded_from.values_list("id", flat=True))
        if self.department.exists():
            employees = employees.filter(job__department__in=self.department.all())
        if self.salary_grade.exists():
            employees = employees.filter(salary_grade__in=self.salary_grade.all())
        if self.designation.exists():
            employees = employees.filter(designation__in=self.designation.all())
        if self.step.exists():
            employees = employees.filter(salary_grade__grade_step__in=self.step.all())

        return employees
    
class PayrollItem(models.Model):
   
    class ItemType(models.TextChoices):
        SALARY_ITEM = "salary_item", "Salary Item"
        LOAN = "loan", "Loan"
        CREDIT_UNION = "credit_union", "Credit Union"
        TAX = "tax", "Tax"
        TAX_RELIEF = "tax_relief", "Tax Relief"
        EMPLOYER_SSNIT = "employer_ssnit", "Employer SSNIT"
        EMPLOYEE_SSNIT = "employee_ssnit", "Employee SSNIT"
        BANK = "bank", "Bank"
        GROSS_SALARY = "gross_salary", "Gross Salary"
        BASIC_SALARY = "basic_salary", "Basic Salary"
        NET_SALARY = "net_salary", "Net Salary"
        STEP = "step", "Step"
        SALARY_GRADE = "salary_grade", "Salary Grade"
        TAXABLE = "taxable", "Taxable"
        EARNING = "earning", "Earning"
        DEDUCTION = "deduction", "Deduction"
        OTHER = "other", "Other"

    payroll = models.ForeignKey('Payroll', on_delete=models.CASCADE, related_name="items")
    employee = models.ForeignKey('hr.Employee', on_delete=models.CASCADE, related_name="payroll_items")
    item_type = models.CharField(max_length=20, choices=ItemType.choices, verbose_name="Item Type")
    dependency = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dependency ID")
    amount = models.DecimalField(max_digits=12, null=True, blank=True, decimal_places=2, verbose_name="Amount")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    ENTRY_TYPES = (
        ('credit', 'Credit'),
        ('debit', 'Debit'), 
        
    )
    entry = models.CharField(max_length=6, null=True, blank=True, choices=ENTRY_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Later addition to avoid complicated queries but make querying more flexible using relationship
    bank = models.ForeignKey('Bank', on_delete=models.SET_NULL, null=True, blank=True, related_name='payroll_items')
    salary_item = models.ForeignKey('SalaryItem', on_delete=models.SET_NULL, null=True, blank=True, related_name='payroll_items')
    loan = models.ForeignKey('Loan', on_delete=models.SET_NULL, null=True, blank=True, related_name='payroll_items')
    credit_union = models.ForeignKey('CreditUnion', on_delete=models.SET_NULL, null=True, blank=True, related_name='payroll_items')


    class Meta:
        verbose_name_plural = "Payroll Items"
        indexes = [
            Index(fields=['payroll', 'item_type'], name='payroll_itemtype_idx'),
            Index(fields=['item_type'], name='item_type_idx'),
            Index(fields=['entry'], name='entry_idx'),
            Index(fields=['dependency'], name='dependency_idx'),
            Index(fields=['payroll', 'dependency'], name='payroll_dependency_idx'),
            Index(fields=['payroll', 'entry'], name='payroll_entry_idx'),  
        ]

    def __str__(self):
        return f"{self.item_type} for {self.employee} in {self.payroll}"

class PayrollError(models.Model):
    payroll = models.ForeignKey('Payroll', on_delete=models.CASCADE, related_name='errors', verbose_name="Related Payroll")
    employee = models.ForeignKey('hr.Employee', on_delete=models.CASCADE, related_name='payroll_errors', verbose_name="Employee")
    ERROR_CATEGORY = (
        ('bank', 'Missing Bank Details'),
        ('salary_grade', 'Missing Salary Grade'),
        ('double_entry', 'Double Entry Failure')
    )
    error_category = models.CharField(max_length=12, choices=ERROR_CATEGORY)
    error_details = models.TextField(null=True, verbose_name="Error Details", help_text="Details of the missing or invalid data.")
    resolved = models.BooleanField(default=False, verbose_name="Is Resolved?")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Error Logged At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Last Updated At")

    class Meta:
        verbose_name = "Payroll Error"
        verbose_name_plural = "Payroll Errors"
        ordering = ['-created_at']

        indexes = [
            Index(fields=['payroll', 'error_category'], name='payroll_errorcategory_idx'),
            Index(fields=['error_category'], name='error_cateogry_idx'),

        ]

    def __str__(self):
        return f"Error for {self.employee} in Payroll {self.payroll}"