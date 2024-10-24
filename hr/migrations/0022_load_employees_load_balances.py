# Generated by Django 5.1.1 on 2024-10-17 21:24

from django.db import migrations


class Migration(migrations.Migration):

    def backfill_leave_balances(apps, schema_editor):
        Employee = apps.get_model('hr', 'Employee')
        LeaveType = apps.get_model('hr', 'LeaveType')
        LeaveBalance = apps.get_model('hr', 'LeaveBalance')

        employees = Employee.objects.all()
        leave_types = LeaveType.objects.all()

        for employee in employees:
            for leave_type in leave_types:
                if not LeaveBalance.objects.filter(employee=employee, leave_type=leave_type).exists():
                    if leave_type.method == 'accrual':
                        LeaveBalance.objects.create(
                            employee=employee,
                            leave_type=leave_type,
                            accrued_days=0.0,
                            used_days=0.0
                        )
                    else:
                        LeaveBalance.objects.create(
                            employee=employee,
                            leave_type=leave_type,
                            accrued_days=leave_type.entitlement,
                            used_days=0.0
                        )

    dependencies = [
        ('hr', '0021_load_leave_types'),
    ]

    operations = [
        migrations.RunPython(backfill_leave_balances)
    ]
