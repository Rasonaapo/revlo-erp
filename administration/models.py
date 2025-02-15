from django.db import models
from hr.models.employee import Employee, Job, Department
from hr.models.payroll import SalaryGrade
from django.utils.translation import gettext_lazy as _
from django_quill.fields import QuillField
from django.utils.timezone import now
import os
from django.utils.text import slugify

class Meeting(models.Model):
    subject = models.CharField(max_length=200)
    meeting_date = models.DateTimeField(verbose_name=_("Meeting Date"))
    sms = models.TextField(null=True, help_text=_("Note: SMS will prepend staff ID and append meeting date & venue"))
    sms_date = models.DateTimeField(verbose_name=_("SMS Date & Time"))
    location = models.CharField(max_length=100, verbose_name=_("Venue"))
    agenda = models.TextField(null=True)
    job = models.ManyToManyField(Job, related_name='meetings')
    department = models.ManyToManyField(Department, related_name='meetings')
    salary_grade = models.ManyToManyField(SalaryGrade, related_name='meetings', verbose_name=_("Salary Grade"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    MEETING_STATUS = (
        ('pending', 'Pending'),
        ('on_going', 'On Going'),
        ('ended', 'Ended'),
    )
    status = models.CharField(choices=MEETING_STATUS, default='pending', max_length=10)
    
    # As we've relocated this model from hr app to this administration app, we must inform Django that this is not entirely new model but relocation
    class Meta:
        db_table = 'hr_meeting'
 
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

class Attendance(models.Model):
    meeting = models.ForeignKey('Meeting', on_delete=models.CASCADE, related_name='attendances')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    check_in_time = models.TimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Attendance of {self.employee} for {self.meeting}"
    
# Models for Business Documents module

class Vendor(models.Model):  # Example Vendor/Supplier table
    name = models.CharField(max_length=255, unique=True, verbose_name=_("Vendor Name"))
    email = models.EmailField(unique=True, null=True, blank=True, verbose_name='Email Address')
    phone_number = models.CharField(max_length=15, blank=True, unique=True, null=True, verbose_name=_("Phone Number"))
    address = models.TextField(blank=True, null=True, verbose_name=_("Address Info"), help_text=_("Provide detailed address, this may include digital address or post address"))
    notes = QuillField(null=True, blank=True, verbose_name=_("Notes"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def format_phone_number(self):
        """Format the phone number to (XXX)-XXXX-XXX format."""
        if self.phone_number and len(self.phone_number) == 10:
            return f"({self.phone_number[:3]})-{self.phone_number[3:7]}-{self.phone_number[7:]}"
        return self.phone_number  # Return unformatted if not 10 digits

class DocumentCategory(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name=_("Category"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
class BusinessDocument(models.Model):
    document_name = models.CharField(max_length=255, unique=True, verbose_name=_("Document Name"))
    associated_entity = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Associated Entity"))
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, blank=True, null=True, related_name="documents", verbose_name=_("Vendor"))
    expiration_date = models.DateField(blank=True, null=True, verbose_name=_("Expiration Date"))
    notes = QuillField(blank=True, null=True, verbose_name=_("Notes"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.document_name

    class Meta:
        verbose_name = _("Business Document")
        verbose_name_plural = _("Business Documents")

def file_upload_path(instance, filename):
    # split filepath to get original name and its extension
        base_filename, file_extension = os.path.splitext(filename)
        timestamp = now().strftime("%Y%m%d%H%M%S")  
        """
          get the name of this business document and prepend it with the base file name..
          Use slugify to replace spaces and special characters with hyphens
        """
        document_name = slugify(instance.business_document.document_name)
        base_filename = slugify(base_filename)

        return f"business_documents/{document_name}_{base_filename}_{timestamp}{file_extension}"

class BusinessDocumentFile(models.Model):
        business_document = models.ForeignKey(BusinessDocument, on_delete=models.CASCADE, related_name='document_files')
        document_category = models.ForeignKey(DocumentCategory, on_delete=models.CASCADE, related_name="document_files", verbose_name=_("Document Category"))
        document_file = models.FileField(upload_to=file_upload_path, verbose_name=_("File"))
        created_at = models.DateTimeField(auto_now_add=True)

        def __str__(self):
            return f"{self.document_category.name} for {self.business_document}"