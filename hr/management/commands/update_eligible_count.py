from django.core.management.base import BaseCommand
from hr.models.payroll import SalaryItem

class Command(BaseCommand):
    help = "Update eligible_employee_count for existing SalaryItem records."

    def handle(self, *args, **kwargs):
        salary_items = SalaryItem.objects.all()
        updated_count = 0

        for item in salary_items:
            eligible_count = item.get_eligible_employees().count()
            if item.eligible_employee_count != eligible_count:
                item.eligible_employee_count = eligible_count
                item.save()
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(f"Updated eligible_employee_count for {updated_count} SalaryItem records."))
