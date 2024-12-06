from django.db import models
from hr.models.employee import Employee, Job, Department
from hr.models.payroll import SalaryGrade

class Meeting(models.Model):
    subject = models.CharField(max_length=200)
    meeting_date = models.DateTimeField(verbose_name="Meeting Date")
    sms = models.TextField(null=True, help_text="Note: SMS will prepend staff ID and append meeting date & venue")
    sms_date = models.DateTimeField(verbose_name="SMS Date & Time")
    location = models.CharField(max_length=100, verbose_name="Venue")
    agenda = models.TextField(null=True)
    job = models.ManyToManyField(Job, related_name='meetings')
    department = models.ManyToManyField(Department, related_name='meetings')
    salary_grade = models.ManyToManyField(SalaryGrade, related_name='meetings', verbose_name="Salary Grade")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    MEETING_STATUS = (
        ('pending', 'Pending'),
        ('on_going', 'On Going'),
        ('ended', 'Ended'),
    )
    status = models.CharField(choices=MEETING_STATUS, default='pending', max_length=10)
    
    # As we've relocated this model from hr app to this administration app, we must inform Django that this is not entirely new model but relocation
    class Meta:
        db_table = 'hr_meeting'
 
    def __str__(self):
        return f"{self.subject} on {self.meeting_date.strftime('%d %b, %Y %I:%M %p')}"
    
    def get_meeting_employees(self):
        # Retrieve the selected criteria
        selected_jobs = self.job.all()
        selected_departments = self.department.all()
        selected_grades = self.salary_grade.all()

        # Filter employees based on the criteria selected
        employees = Employee.objects.all()
        filtered_employees = [
            employee for employee in employees
            if (not selected_jobs or employee.job in selected_jobs) and 
               (not selected_departments or (employee.job and employee.job.department in selected_departments )) and 
               (not selected_grades or employee.salary_grade in selected_grades)
        ]
        return filtered_employees
    
    def display_meeting_job(self):
        return ",".join(job.job_title for job in self.job.all())

    def display_meeting_department(self):
        return ",".join(department.department_name for department in self.department.all())

    def display_meeting_grade(self):
        return ",".join(grade.grade for grade in self.salary_grade.all())

class Attendance(models.Model):
    meeting = models.ForeignKey('Meeting', on_delete=models.CASCADE, related_name='attendances')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    check_in_time = models.TimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Attendance of {self.employee} for {self.meeting}"