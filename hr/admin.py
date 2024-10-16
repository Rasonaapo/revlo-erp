from django.contrib import admin

# Register your models here.
from .models.employee import *
from .models.payroll import *

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'employee_id', 'status',  'photo', 'email', 'phone_number', 'hire_date', 'salary_grade', 'job', 'ssnit', 'tin', 'bank', 'branch', 'account_number', 'id_type', 'id_number', )

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('department_name', 'manager', 'location', )

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('job_title', 'department', 'min_salary', 'max_salary', )

@admin.register(JobHistory)
class JobHistoryAdmin(admin.ModelAdmin):
    list_display = ('employee', 'start_date', 'end_date', 'job', )

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'document_type', 'document_file')

@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'allow_multiple', )

@admin.register(NationalIDType)
class NationalIDTypeAdmin(admin.ModelAdmin):
    list_display = ('name', )

@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ('subject', 'meeting_date', 'sms_date', 'location', 'agenda', )

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('meeting', 'employee', 'check_in_time', )

# Payroll
@admin.register(SalaryGrade) 
class SalaryGradeAdmin(admin.ModelAdmin):
    list_display = ('grade', 'step', 'amount', )

@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ('bank_name', 'active', )

@admin.register(Guarantor)
class GuarantorAdmin(admin.ModelAdmin):
    list_display = ('employee', 'guarantor_name', 'guarantor_phone_number', )

@admin.register(Tax)
class TaxAdmin(admin.ModelAdmin):
    list_display = ('year', 'block', 'rate', )

