from django.contrib import admin

# Register your models here.
from .models.employee import *
from .models.payroll import *

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'employee_id', 'status',  'photo', 'email', 'phone_number', 'hire_date', 'salary_grade', 'job', 'ssnit', 'tin', 'bank', 'branch', 'account_number', 'id_type', 'id_number','display_employee_skill')
    list_filter = ['skills']

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('department_name', 'manager', 'location', )

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('job_title', 'department', 'min_salary', 'max_salary', )

@admin.register(JobHistory)
class JobHistoryAdmin(admin.ModelAdmin):
    list_display = ('employee', 'start_date', 'end_date', 'job',  'designation')

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
    list_display = ('subject', 'meeting_date', 'sms_date', 'location', 'status', 'agenda', )

@admin.register(SMS)
class SMSAdmin(admin.ModelAdmin):
    list_display = ('message', 'sms_date', 'display_sms_job', 'display_sms_department', 'display_sms_grade', 'created_at', 'updated_at', 'status', )

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('meeting', 'employee', 'check_in_time', )

# Payroll
@admin.register(SalaryGrade) 
class SalaryGradeAdmin(admin.ModelAdmin):
    list_display = ('grade', 'step', 'grade_step', 'amount', )

@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ('bank_name', 'active', )

@admin.register(Guarantor)
class GuarantorAdmin(admin.ModelAdmin):
    list_display = ('employee', 'guarantor_name', 'guarantor_phone_number', )

@admin.register(Tax)
class TaxAdmin(admin.ModelAdmin):
    list_display = ('year', 'block', 'rate', )

# Leave
@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'entitlement', 'method', 'allow_rollover' )

@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'accrued_days', 'used_days', )

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'status', 'days_requested', )

@admin.register(PublicHoliday)
class PublicHolidayAdmin(admin.ModelAdmin):
    list_display = ('name', 'date')
    list_filter = ['date']

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ['category']

@admin.register(SalaryStep)
class SalaryStepAdmin(admin.ModelAdmin):
    list_display = ['step']

@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'level', )

@admin.register(SalaryItem)
class SalaryItemAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'alias_name', 'effect', 'rate_type', 'rate_amount', 'rate_dependency', 'staff_source', )

@admin.register(StaffSalaryItem)
class StaffSalaryItemAdmin(admin.ModelAdmin):
    list_display = ('salary_item', 'employee', 'variable', 'amount', 'active', )

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('employee', 'loan_type', 'principal_amount', 'interest_rate', 'monthly_installment', 'status')
    list_filter = ('loan_type', 'status')
    search_fields = ('employee__first_name', 'employee__last_name')
