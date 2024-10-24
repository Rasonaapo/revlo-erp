from django.core.management.base import BaseCommand
from hr.models.employee import PublicHoliday
from datetime import date
from django.db import transaction

class Command(BaseCommand):
    help = 'Update public holiday dates to the current year on January 1st'

    def handle(self, *args, **kwargs):
        # Get the current year
        current_year = date.today().year

        # Fetch all public holidays
        holidays = PublicHoliday.objects.all()
        
        with transaction.atomic():
            for holiday in holidays:
                # Update the year of the holiday to the current year
                holiday_date = holiday.date
                updated_holiday_date = holiday_date.replace(year=current_year)

                # Update the holiday's date and save it
                holiday.date = updated_holiday_date
                holiday.save()

        self.stdout.write(self.style.SUCCESS(f"Public holidays updated to the year {current_year}"))




