from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from hr.models.employee import Meeting, Employee
from django.db.models import Q

class Command(BaseCommand):
    help = "Dispatch SMS reminders for meetings scheduled for today"

    def handle(self, *args, **kwargs):
        today = timezone.now()
        meetings = Meeting.objects.filter(
            sms_date__date=today.date(),
            sms_date__hour=today.hour,
            sms_date__minute=today.minute,
            status='pending'
        )

        with transaction.atomic():
            for meeting in meetings:
                employees = meeting.get_meeting_employees()
                message_template = meeting.sms

                for employee in employees:
                    # Prepend ID and append meeting location
                    message = f"{employee.employee_id}: {message_template} - Venue: {meeting.location}"
                    
                    # call  SMS API here
                    self.send_sms(employee.phone_number, message)

                # Update meeting status to 'on_going' (assuming the meeting starts today)
                meeting.status = 'on_going'
                meeting.save(update_fields=['status'])
            
            self.stdout.write(self.style.SUCCESS("Meeting SMS dispatch completed."))

    def send_sms(self, phone_number, message):
        # call  SMS API here
        print(f"Sending SMS to {phone_number}: {message}")
