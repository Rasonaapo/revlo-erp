from datetime import timedelta
from hr.models.employee import PublicHoliday
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
