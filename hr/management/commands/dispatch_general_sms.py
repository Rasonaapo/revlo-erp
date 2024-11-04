from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from hr.models.employee import SMS
from django.db.models import Q

class Command(BaseCommand):
    help = "Dispatch general SMS messages scheduled for today"

    def handle(self, *args, **kwargs):
        today = timezone.now()
        sms_records = SMS.objects.filter(
            sms_date__date=today.date(),
            sms_date__hour=today.hour,
            sms_date__minute=today.minute,
            status='pending'
        )
        with transaction.atomic():
            for sms in sms_records:
                employees = sms.get_sms_employees()
                message_template = sms.message

                for employee in employees:
                    # We prepend ID to each message
                    message = f"Hi {employee.employee_id}: {message_template}"
                    
                    # call  SMS API here
                    self.send_sms(employee.phone_number, message)

                # Update SMS record status to 'dispatched'
                sms.status = 'dispatched'
                sms.save(update_fields=['status'])

            self.stdout.write(self.style.SUCCESS("General SMS dispatch completed."))

    def send_sms(self, phone_number, message):
        # call  SMS API here
        print(f"Sending SMS to {phone_number}: {message}")
