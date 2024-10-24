from django.core.management.base import BaseCommand
from hr.models.employee import LeaveBalance, LeaveType
from datetime import date 
from django.db import transaction

class Command(BaseCommand):
    help = 'Reset leave entitlements for static leave types on January 1st'

    def handle(self, *args, **kwargs):
        # Fetch leave balances with static method
        static_balances = LeaveBalance.objects.filter(leave_type__method='fixed')
        
        with transaction.atomic():
            for balance in static_balances:
                if balance.leave_type.allow_rollover:
                    # Apply rollover (add remaining days to new entitlement)
                    remaining_days = balance.remaining_days()
                    balance.accrued_days = min(remaining_days, balance.leave_type.entitlement) + balance.leave_type.entitlement
                else:
                    # Reset to the new entitlement
                    balance.accrued_days = balance.leave_type.entitlement
                
                balance.used_days = 0  # Reset used days for the new year
                balance.save()

        self.stdout.write(self.style.SUCCESS(f'Leave balances reset for {date.today().year}'))
