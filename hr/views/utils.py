from datetime import timedelta
from hr.models.employee import PublicHoliday, Employee
from hr.models.payroll import SalaryItem
from datetime import datetime

def calculate_end_date(start_date, days_requested):
    days_remaining = days_requested
    end_date = start_date

    while days_remaining > 0:
        # Increment the end_date by 1 day
        end_date += timedelta(days=1)
        
        # Check if the current end_date is a weekday and not a public holiday
        if end_date.weekday() < 5 and not PublicHoliday.objects.filter(date=end_date).exists():
            days_remaining -= 1  # Only count weekdays and non-holidays towards requested days
    
    return end_date

def get_current_year():
    return datetime.now().year

def item_expiry_status(expiry_date):
   today = datetime.now().date()
   return today < expiry_date

def compute_factor(employee, rate_amount, rate_dependency):
    basic_salary = employee.salary_grade.amount

    # if rate dependency is Basic, use rate amount to get the percentage of that..
    if rate_dependency == 'Basic':
        amount = (rate_amount / 100) * basic_salary
    else:
        # get the rate amount of the selected item whose id is rate dependency
        salary_item = SalaryItem.objects.get(id=rate_dependency)
        amount = (rate_amount / 100) * salary_item.rate_amount
    
    return amount

# a method to synthetically retrieve eligible employees for credit union to make update seamless with transactions
def get_filtered_staff_credit_union(all_employee, department, applicable_to, excluded_from):

    eligible_employee = Employee.objects.active()

    # if all employee is checked, return all
    if all_employee:
        return eligible_employee
    
    # Navigate through the filters if not all employee was specified
    if department.exists():
        eligible_employee = eligible_employee.filter(job__department__in=department.all())
    if applicable_to.exists():
        eligible_employee = applicable_to.all()
    if excluded_from.exists():
        eligible_employee = eligible_employee.exclude(id__in=excluded_from.values_list('id', flat=True))

    return eligible_employee

def get_filtered_staff_payroll(data):
    eligible_employee = Employee.objects.active()

    if data['condition'] != 'all':
        eligible_employee = eligible_employee.filter(employment_type=data['condition'])
    
    if data['step'].exists():
        eligible_employee = eligible_employee.filter(salary_grade__grade_step__in=data['step'].all())

    if data['salary_grade'].exists():
        eligible_employee = eligible_employee.filter(salary_grade__in=data['salary_grade'].all())
    
    if data['designation'].exists():
        eligible_employee = eligible_employee.filter(designation__in=data['designation'].all())

    if data['department'].exists():
        eligible_employee = eligible_employee.filter(job__department__in=data['department'].all())
    
    if data['applicable_to'].exists():
        eligible_employee = eligible_employee.filter(id__in=data['applicable_to'].values_list('id', flat=True))
    
    if data['excluded_from'].exists():
        eligible_employee = eligible_employee.exclude(id__in=data['excluded_from'].values_list('id', flat=True))

    return eligible_employee

    

