from django.core.management.base import BaseCommand
from datetime import date
from hr.models.employee import LeaveRequest, Employee
from django.core.exceptions import ValidationError
from django.db import transaction

class Command(BaseCommand):
    help = 'Send SMS reminders and update employee status for leaves starting or ending today'

    def handle(self, *args, **kwargs):
        today = date.today()
        
        # Check for leaves that end today
        ending_today = LeaveRequest.objects.filter(end_date=today, status='Approved')
        for leave in ending_today:
            # Send SMS to remind the employee that leave ends today
            self.send_sms_reminder(leave.employee, 'Your leave ends today. Please resume work tomorrow.')
        
        # Check for leaves that start today and update employee status to 'on_leave'
        starting_today = LeaveRequest.objects.filter(start_date=today, status='Approved')
        with transaction.atomic():
            for leave in starting_today:
                # Update employee status
                employee = leave.employee
                employee.status = Employee.Status.ON_LEAVE
                employee.save()
                
                # Send SMS to remind the employee
                self.send_sms_reminder(leave.employee, 'Your leave starts today. Have a restful break.')

        self.stdout.write(self.style.SUCCESS(f'Leave reminders processed for {today}'))

    def send_sms_reminder(self, employee, message):
        # We will use mnofity
        print(f"SMS sent to {employee.phone_number}: {message}")
