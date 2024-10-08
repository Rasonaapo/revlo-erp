from django.contrib import admin

# Register your models here.
from .models.employee import *
from .models.payroll import *

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'photo', 'email', 'phone_number', 'hire_date', 'salary_grade', 'department', )

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('department_name', 'manager', 'location', )

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('job_title', 'min_salary', 'max_salary', )

@admin.register(JobHistory)
class JobHistoryAdmin(admin.ModelAdmin):
    list_display = ('employee', 'start_date', 'end_date', 'job', 'department', )

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'document_name', 'document_file', )

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