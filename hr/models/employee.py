from django.db import models
from django.contrib.auth import get_user_model
from hr.models.payroll import SalaryGrade, Bank
from datetime import date
from django.utils.timezone import now
import os
from django.utils.text import slugify
from PIL import Image
from django.core.exceptions import ValidationError
from django.urls import reverse
from django_quill.fields import QuillField
from django.db.models import Index

User = get_user_model()

def employee_photo_upload_path(instance, filename):
    """
    Construct a file path for uploaded photos using the employee's name and current timestamp.
    Replaces spaces with underscores to avoid issues in file names.
    """
    base_filename, file_extension = os.path.splitext(filename)
    timestamp = now().strftime("%Y%m%d%H%M%S")  

    # Use slugify to replace spaces and special characters with hyphens
    first_name = slugify(instance.first_name)
    last_name = slugify(instance.last_name)

    return f'photos/{first_name}_{last_name}_{timestamp}{file_extension}'   

class NationalIDType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name

class EmployeeQuerySet(models.QuerySet):
    def active(self):
        """Returns only employees with valid active statuses."""
        valid_statuses = ['active', 'on_leave', 'probation']
        return self.filter(status__in=valid_statuses)

class EmployeeManager(models.Manager):
    def get_queryset(self):
        return EmployeeQuerySet(self.model, using=self._db)

    def active(self):
        """Shortcut to query only active employees."""
        return self.get_queryset().active()
    
class Employee(models.Model):
    # user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        ON_LEAVE = 'on_leave', 'On Leave'
        TERMINATED = 'terminated', 'Terminated'
        PROBATION = 'probation', 'Probation'
        RETIRED = 'retired', 'Retired'
        RESIGNED = 'resigned', 'Resigned'
    first_name = models.CharField(max_length=50, verbose_name='First Name')
    last_name = models.CharField(max_length=50, verbose_name='Surname')
    employee_id = models.CharField(max_length=12, null=True, unique=True, verbose_name='Staff ID')
    dob = models.DateField(verbose_name='Birth Date', null=True)
    id_type = models.ForeignKey(NationalIDType, on_delete=models.SET_NULL, null=True, verbose_name="National ID")
    id_number = models.CharField(max_length=24, null=True, blank=True, verbose_name="ID Number")
    # photo = models.ImageField(upload_to='photos/', null=True, default="avatar.png")
    photo = models.ImageField(upload_to=employee_photo_upload_path, null=True, default="avatar.png")

    email = models.EmailField(unique=True, verbose_name='Email Address')
    phone_number = models.CharField(max_length=15, unique=True, verbose_name='Phone Number')
    salary_grade = models.ForeignKey(SalaryGrade, on_delete=models.DO_NOTHING, null=True, verbose_name='Salary Grade', related_name='employees')
    bank = models.ForeignKey(Bank, on_delete=models.DO_NOTHING, null=True, related_name='employees')
    account_number = models.CharField(max_length=24, unique=True, null=True, verbose_name='Account Number')
    branch = models.CharField(max_length=254, null=True, verbose_name='Branch')
    tin = models.CharField(max_length=24, unique=True, null=True, verbose_name='TIN No.')
    ssnit = models.CharField(max_length=24, null=True, unique=True, verbose_name='SSNIT No.')
    hire_date = models.DateField(verbose_name='Hired Date')
    job = models.ForeignKey('Job', on_delete=models.SET_NULL, null=True, related_name='employees')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    skills = models.ManyToManyField('Skill', related_name='employees', blank=True)
    EMPLOYMENT_TYPE = (
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contractual', 'Contractual'),
        ('temporary', 'Temporary')
    )
    employment_type = models.CharField(max_length=12, choices=EMPLOYMENT_TYPE, default='full_time')
    designation = models.ForeignKey('Designation', null=True, on_delete=models.SET_NULL, related_name='employees')
    tax_relief = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Tax Relief")
    # Custom Manager
    objects = EmployeeManager()
    
    def __str__(self):
        return f"{self.first_name.capitalize()} {self.last_name.capitalize()}"
    
    def missing_skills(self):
        """Return a set skills required by the job but not possesed by the employee"""
        job_skills = set(self.job.required_skills.all()) if self.job else set()
        employee_skills = set(self.skills.all())
        missing_skills = job_skills - employee_skills
        return ",".join(skill.name for skill in missing_skills)

    def display_employee_skill(self):
        return ",".join(skill.name for skill in self.skills.all())

    def get_absolute_url(self):
        return reverse("employee-detail", args=[str(self.id)])
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Save the instance first to get a file path

        # Open the image using Pillow
        img = Image.open(self.photo.path)

        # Resize the image (maintaining aspect ratio), let's say to a maximum width of 800px
        max_size = (800, 800)  # Define a maximum size (width, height)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)  # Use LANCZOS instead of ANTIALIAS

        # Save the image back to the file path, reducing quality to 85% for space efficiency
        img.save(self.photo.path, quality=85)

    class Meta:
        unique_together = ('id_type', 'id_number')
        indexes = [
            Index(fields=['first_name', 'last_name'], name='name_idx'),
            Index(fields=['email'], name='email_idx'),
            Index(fields=['phone_number'], name='phone_number_idx'),
        ]  

    def get_age(self):
        """Calculate the employee's age based on their date of birth."""
        today = date.today()
        if self.dob:
            # Calculate age considering year and month
            age = today.year - self.dob.year
            if today.month < self.dob.month or (today.month == self.dob.month and today.day < self.dob.day):
                age -= 1
            return age
        return None  # Handle cases where dob might be null

    def format_phone_number(self):
        """Format the phone number to (XXX)-XXXX-XXX format."""
        if self.phone_number and len(self.phone_number) == 10:
            return f"({self.phone_number[:3]})-{self.phone_number[3:7]}-{self.phone_number[7:]}"
        return self.phone_number  # Return unformatted if not 10 digits

class Guarantor(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='guarantors')
    guarantor_name = models.CharField(max_length=100, verbose_name='Guarantor Name')
    guarantor_phone_number = models.CharField(max_length=15, unique=True, verbose_name='Guarantor Phone Number')
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        unique_together = ('employee', 'guarantor_name', 'guarantor_phone_number')

    def __str__(self):
        return f"Guarantor: {self.guarantor_name} ({self.guarantor_phone_number})"
    
    def format_phone_number(self):
        """Format the phone number to (XXX)-XXXX-XXX format."""
        if self.guarantor_phone_number and len(self.guarantor_phone_number) == 10:
            return f"({self.guarantor_phone_number[:3]})-{self.guarantor_phone_number[3:7]}-{self.guarantor_phone_number[7:]}"
        return self.guarantor_phone_number  # Return unformatted if not 10 digits


class Department(models.Model):
    department_name = models.CharField(max_length=100, unique=True)
    manager = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_departments')
    location = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.department_name

class Job(models.Model):
    CURRENCY_CHOICES = [
        ('USD', 'US Dollars'),
        ('EUR', 'Euros'),
        ('GBP', 'British Pounds'),
        ('GHS', 'Ghanaian Cedi'),
        # We will add more currencies as needed
    ]
    job_title = models.CharField(max_length=100)
    min_salary = models.DecimalField(max_digits=10, decimal_places=2)
    max_salary = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='GHS')
    department = models.ForeignKey(Department, null=True, on_delete=models.CASCADE, related_name='jobs')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    responsibilities = QuillField(null=True, blank=True)
    required_skills = models.ManyToManyField('Skill', related_name="required_for_jobs")

    def __str__(self):
        return self.job_title
    
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
    
    def display_required_skills(self):
        return ",".join(skill.name for skill in self.required_skills.all())
    
class JobHistory(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='job_history')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='job_history')
    designation = models.ForeignKey('Designation', null=True, blank=True, on_delete=models.CASCADE, related_name='job_history')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee} - {self.job} ({self.start_date} to {self.end_date})"

class DocumentType(models.Model):
    """
    This model holds predefined types of documents such as 'CV', 'Certificate', etc.
    """
    name = models.CharField(max_length=100, unique=True)
    allow_multiple = models.BooleanField(default=False, help_text="Allow multiple documents of this type per employee?")
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name
    
class Document(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='documents')
    document_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE, null=True,  related_name='documents')
    document_file = models.FileField(upload_to='documents/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.document_type.name} - {self.employee}"

class Meeting(models.Model):
    subject = models.CharField(max_length=200)
    meeting_date = models.DateTimeField(verbose_name="Meeting Date")
    sms = models.TextField(null=True, help_text="Note: SMS will prepend staff ID and append meeting date & venue")
    sms_date = models.DateTimeField(verbose_name="SMS Date & Time")
    location = models.CharField(max_length=100, verbose_name="Venue")
    agenda = models.TextField(null=True)
    job = models.ManyToManyField('Job', related_name='meetings')
    department = models.ManyToManyField('Department', related_name='meetings')
    salary_grade = models.ManyToManyField('SalaryGrade', related_name='meetings', verbose_name="Salary Grade")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    MEETING_STATUS = (
        ('pending', 'Pending'),
        ('on_going', 'On Going'),
        ('ended', 'Ended'),
    )
    status = models.CharField(choices=MEETING_STATUS, default='pending', max_length=10)

    def __str__(self):
        return f"{self.subject} on {self.meeting_date.strftime('%d %b, %Y %I:%M %p')}"
    
    def get_meeting_employees(self):
        # Retrieve the selected criteria
        selected_jobs = self.job.all()
        selected_departments = self.department.all()
        selected_grades = self.salary_grade.all()

        # Filter employees based on the criteria selected
        employees = Employee.objects.all()
        filtered_employees = [
            employee for employee in employees
            if (not selected_jobs or employee.job in selected_jobs) and 
               (not selected_departments or (employee.job and employee.job.department in selected_departments )) and 
               (not selected_grades or employee.salary_grade in selected_grades)
        ]
        return filtered_employees
    
    def display_meeting_job(self):
        return ",".join(job.job_title for job in self.job.all())

    def display_meeting_department(self):
        return ",".join(department.department_name for department in self.department.all())

    def display_meeting_grade(self):
        return ",".join(grade.grade for grade in self.salary_grade.all())

class SMS(models.Model):
    message = models.TextField(null=True, help_text="Note: SMS will prepend staff ID")
    sms_date = models.DateTimeField(verbose_name="SMS Date & Time")
    job = models.ManyToManyField('Job', related_name='sms')
    department = models.ManyToManyField('Department', related_name='sms')
    salary_grade = models.ManyToManyField('SalaryGrade', related_name='sms', verbose_name="Salary Grade")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    SMS_STATUS = (
        ('pending', 'Pending'),
        ('dispatched', 'Dispatched'),
    )
    status = models.CharField(choices=SMS_STATUS, default='pending', max_length=10)

    class Meta:
        verbose_name_plural = 'Sms'

    def __str__(self):
        return f"{self.message[:20]} on {self.sms_date.strftime('%d %b, %Y %I:%M %p')}"
    
    def get_sms_employees(self):
        # Retrieve the selected criteria
        selected_jobs = self.job.all()
        selected_departments = self.department.all()
        selected_grades = self.salary_grade.all()

        # Filter employees based on the criteria selected
        employees = Employee.objects.all()
        filtered_employees = [
            employee for employee in employees
            if (not selected_jobs or employee.job in selected_jobs) and 
               (not selected_departments or (employee.job and employee.job.department in selected_departments )) and 
               (not selected_grades or employee.salary_grade in selected_grades)
        ]
        return filtered_employees
    
    def display_sms_job(self):
        return ",".join(job.job_title for job in self.job.all())

    def display_sms_department(self):
        return ",".join(department.department_name for department in self.department.all())

    def display_sms_grade(self):
        return ",".join(grade.grade for grade in self.salary_grade.all())
    
class Attendance(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='attendances')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    check_in_time = models.TimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Attendance of {self.employee} for {self.meeting}"

class LeaveType(models.Model):
    LEAVE_METHOD_CHOICES = [
        ('accrual', 'Accrual Method'),
        ('fixed', 'Static Annual Allotment'),
    ]
    
    name = models.CharField(max_length=50)
    entitlement = models.FloatField()  # Entitlement in days (used for both methods)
    method = models.CharField(max_length=10, choices=LEAVE_METHOD_CHOICES, default='accrual')  # Which method is used for this leave type
    allow_rollover = models.BooleanField(default=False, verbose_name="Allow Rollover")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class LeaveBalance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    accrued_days = models.FloatField(default=0.0)  # For accrual method
    used_days = models.FloatField(default=0.0)     # For both methods
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def remaining_days(self):
        # if self.leave_type.method == 'accrual':
        # Always return accrued days minus used days, regardless of method
        return self.accrued_days - self.used_days
        # else:
        #     # For static allotment, use entitlement directly
        #     return self.leave_type.entitlement - self.used_days

    def accrue_leave(self, months_worked):
        if self.leave_type.method == 'accrual':
            # Accrual method: leave increases month by month
            annual_entitlement = self.leave_type.entitlement
            self.accrued_days += (annual_entitlement / 12) * months_worked
        # For static allotment, leave balance is already pre-set at the start of the year.
        self.save()

    def __str__(self):
        return f"{self.employee} - {self.leave_type.name} leave balance"
    
class LeaveRequest(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected'), ('Expired', 'Expired')], default='Pending')
    days_requested = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        leave_balance = LeaveBalance.objects.get(employee=self.employee, leave_type=self.leave_type)
        
        if self.status == 'Approved':
            if leave_balance.remaining_days() >= self.days_requested:
                leave_balance.used_days += self.days_requested
                leave_balance.save()
                super().save(*args, **kwargs)
            else:
                raise ValidationError(f"Insufficient leave balance for {self.leave_type.name}. Available balance: {leave_balance.remaining_days()} days.")
        else:
            super().save(*args, **kwargs)


class PublicHoliday(models.Model):
    name = models.CharField(max_length=255, unique=True)  # Name of the holiday (e.g., Christmas, New Year)
    date = models.DateField()  # The date of the holiday
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('name', 'date')  # Ensure a holiday with the same name and date cannot be duplicated

    def __str__(self):
        return f"{self.name} ({self.date.strftime('%d %b, %Y')})"

class Skill(models.Model):
    SKILL_CATEGORY_CHOICES = [
    ('technical', 'Technical Skills'),
    ('project_management', 'Project Management & Leadership'),
    ('marketing', 'Marketing & Sales'),
    ('finance', 'Finance & Accounting'),
    ('hr', 'Human Resources'),
    ('design', 'Design & Creative'),
    ('customer_service', 'Customer Service & Support'),
    ('operations', 'Operations & Supply Chain'),
    ('legal', 'Legal & Compliance'),
    ('soft_skills', 'Soft Skills'),
    ('languages', 'Languages'),
]
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=SKILL_CATEGORY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('name', 'category')

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"  # Show skill with category in string representation

class Designation(models.Model):
    code = models.CharField(max_length=12, null=True, unique=True)
    title = models.CharField(max_length=100, verbose_name="Title/Rank", unique=True)
    level = models.CharField(max_length=100, null=True, verbose_name="Hierarchy Level")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.level})"

    class Meta:
        unique_together = ('title', 'level')