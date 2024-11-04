from django.core.management.base import BaseCommand
from datetime import date, timedelta
from hr.models.employee import LeaveRequest, Employee
from django.db import transaction

class Command(BaseCommand):
    help = 'Mark leave requests as expired if they ended yesterday'

    def handle(self, *args, **kwargs):
        yesterday = date.today() - timedelta(days=1)
        
        # Find leave requests that ended yesterday and update their status
        expired_leaves = LeaveRequest.objects.filter(end_date__lt=date.today(), status='Approved')
        with transaction.atomic():
            for leave in expired_leaves:
                leave.status = 'Expired'
                leave.save()

                # Update employee status back to 'Active'
                employee = leave.employee
                employee.status = Employee.Status.ACTIVE
                employee.save()

        self.stdout.write(self.style.SUCCESS(f'Leave statuses updated to expired for {yesterday}'))
