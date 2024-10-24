from django.core.management.base import BaseCommand
from hr.models.employee import LeaveBalance, LeaveType
from datetime import date
from dateutil.relativedelta import relativedelta  # This helps us easily calculate date differences
from django.db import transaction

class Command(BaseCommand):
    help = 'Accrue leave for all employees with accrual-based leave types at the end of the month'

    def handle(self, *args, **kwargs):
        # Fetch leave balances with accrual method
        accrual_balances = LeaveBalance.objects.filter(leave_type__method='accrual')
        
        today = date.today()
        with transaction.atomic():
            for balance in accrual_balances:
                # Deduce months worked using the employee's hire_date
                hire_date = balance.employee.hire_date
                
                # Calculate months worked as the difference between today and the hire date
                months_worked = relativedelta(today, hire_date).months + (relativedelta(today, hire_date).years * 12)

                # Calculate monthly accrual based on months worked
                balance.accrue_leave(months_worked=months_worked)
                balance.save()

        self.stdout.write(self.style.SUCCESS(f'Monthly leave accrual completed for {today}'))

