from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from hr.models.employee import Employee, Department
from django_datatables_view.base_datatable_view import BaseDatatableView
from django.utils.html import escape
from datetime import date
from django.db.models import Q, Count
import json
from django.urls import reverse

# Employee
class EmployeeListApiView(LoginRequiredMixin, BaseDatatableView):
    model = Employee
    columns = ['id', 'first_name', 'last_name', 'employee_id', 'status', 'dob', 'phone_number', 'job', 'hire_date', 'salary_grade', 'created_at']

    def render_column(self, row, column):
        print(f"Row Data: {row.id} {column}")  # This will print the entire row object

        if column == 'photo':
            return row.photo.url
        
        if column == 'dob':
            return row.get_age()
        
        if column == 'job':
            return row.job.job_title
        
        if column == 'created_at':
            return row.created_at.strftime('%d %b, %Y')  # Format the created_at field

        if column == 'hire_date':
            return row.hire_date.strftime('%d %b, %Y')  # Format the created_at field

        if column == 'phone_number':
            return row.format_phone_number()  # Format the created_at field

        if column == 'salary_grade':
            return row.salary_grade.grade
        if column == 'status':
            status = 'success'
            if row.status == 'inactive':
                status = 'dark'
            elif row.status == 'on_leave':
                status = 'warning'
            elif row.status == 'terminated':
                status = 'danger label-table'
            elif row.status == 'probation':
                status = 'info'
            elif row.status == 'retired':
                status = 'primary'
            elif row.status == 'resigned':
                status = 'danger'

            return f"<span class='badge bg-{status}'>{row.get_status_display()}</span>"
        
        if column == 'first_name':  # Display employee photo with name
            photo_url = row.photo.url
            url = reverse('employee-detail', args=[row.id])

            return f'<img src="{photo_url}"  alt="contact-img" title="contact-img" class="rounded-circle me-2 avatar-sm"> <a href="{url}" class="text-body fw-semibold">{row.first_name} {row.last_name}</a>'
        
        if column == 'id':
            return row.id
        
        return super().render_column(row, column)

    def get_initial_queryset(self):
        return Employee.objects.all()
    
    def filter_queryset(self, qs):
        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(employee_id__icontains=search) |
                Q(phone_number__icontains=search) |
                Q(department__department_name__icontains=search) |
                Q(salary_grade__grade__icontains=search)

            )
        return qs
 
# Department

class DepartmentListApiView(LoginRequiredMixin, BaseDatatableView):
    model = Department
    columns = ['id', 'department_name', 'manager', 'location', 'employee_count', 'created_at']

    def render_column(self, row, column):
        if column == 'created_at':
            return row.created_at.strftime('%d %b, %Y')  # Format the created_at field
        
        if column == 'manager':  # Display employee photo with name
            if row.manager is None:
                return 'N/A'
            else:
                photo_url = row.manager.photo.url
                return f'<img src="{photo_url}"  alt="contact-img" title="contact-img" class="rounded-circle me-2" heigth="20px" width="30px"> {row.manager.first_name} {row.manager.last_name}'
        
        if column == 'id':
            return row.id
        
        if column == 'employee_count':
            return row.employee_count or '-'
        
        return super().render_column(row, column)

    def get_initial_queryset(self):
        return Department.objects.annotate(employee_count=Count('jobs__employees'))
    
    def filter_queryset(self, qs):
        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(department_name__icontains=search) |
                Q(manager__last_name__icontains=search) |
                Q(manager__first_name__icontains=search) |
                Q(location__icontains=search)

            )
        return qs