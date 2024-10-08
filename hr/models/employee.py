from django.db import models
from django.contrib.auth import get_user_model
from hr.models.payroll import SalaryGrade, Bank
from datetime import date
from django.utils.timezone import now
import os
from django.utils.text import slugify
from PIL import Image

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

class Employee(models.Model):
    # user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    first_name = models.CharField(max_length=50, verbose_name='First Name')
    last_name = models.CharField(max_length=50, verbose_name='Surname')
    employee_id = models.CharField(max_length=12, null=True, unique=True, verbose_name='Staff ID')
    dob = models.DateField(verbose_name='Birth Date', null=True)
    # photo = models.ImageField(upload_to='photos/', null=True, default="avatar.png")
    photo = models.ImageField(upload_to=employee_photo_upload_path, null=True, default="avatar.png")

    email = models.EmailField(unique=True, verbose_name='Email Address')
    phone_number = models.CharField(max_length=15, verbose_name='Phone Number')
    salary_grade = models.ForeignKey(SalaryGrade, on_delete=models.DO_NOTHING, null=True, verbose_name='Salary Grade', related_name='employees')
    bank = models.ForeignKey(Bank, on_delete=models.DO_NOTHING, null=True, related_name='employees')
    account_number = models.CharField(max_length=24, null=True, verbose_name='Account Number')
    branch = models.CharField(max_length=254, null=True, verbose_name='Branch')
    tin = models.CharField(max_length=24, unique=True, null=True, verbose_name='TIN No.')
    ssnit = models.CharField(max_length=24, null=True, unique=True, verbose_name='SSNIT No.')
    hire_date = models.DateField(verbose_name='Hired Date')
    department = models.ForeignKey('Department', on_delete=models.CASCADE, related_name='employees')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
        unique_together = ()

    def __str__(self):
        return f"{self.first_name.capitalize()} {self.last_name.capitalize()}"
    

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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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

class JobHistory(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='job_history')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='job_history')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='job_history')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee} - {self.job} ({self.start_date} to {self.end_date})"

class Document(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='documents')
    document_name = models.CharField(max_length=100)
    document_file = models.FileField(upload_to='documents/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.document_name} - {self.employee}"

class Meeting(models.Model):
    subject = models.CharField(max_length=200)
    meeting_date = models.DateTimeField()
    sms_date = models.DateTimeField()
    location = models.CharField(max_length=100)
    agenda = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.subject} on {self.meeting_date}"

class Attendance(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='attendances')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    check_in_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Attendance of {self.employee} for {self.meeting}"


# class Salary(models.Model):
#     employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='salary_records')
#     amount = models.DecimalField(max_digits=10, decimal_places=2)
#     payment_date = models.DateField()
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"{self.employee} - {self.amount} on {self.payment_date}"
