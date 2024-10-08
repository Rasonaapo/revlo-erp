from django.db.models.query import QuerySet
from django.forms import BaseModelForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.views.generic import ListView, CreateView, UpdateView
from hr.models.employee import *
from django.urls import reverse_lazy
from django import forms
from ..forms.employee_forms import JobHistoryForm, EmployeeForm

# Create your views here.
class DepartmentListView(LoginRequiredMixin, ListView):
    model = Department
    template_name = 'hr/employee/department_list.html'
    context_object_name = 'department_list'

    def get_queryset(self):
       queryset = super().get_queryset()
       queryset = queryset.order_by('created_at')
       return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Departments'
        return context

class DepartmentCreateView(LoginRequiredMixin, CreateView):
    model = Department
    template_name = 'hr/employee/department_form.html'
    fields = ['department_name', 'manager', 'location']  
    success_url = reverse_lazy('department-list')  

    # Override the form fields
    def get_form(self, *args, **kwargs):
        form = super(DepartmentCreateView, self).get_form(*args, **kwargs)
        # Make the manager field required in the form even though it's optional in the model
        # form.fields['manager'].required = True
        return form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Department'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, f'Department [{form.instance.department_name}] created successfully.')
        return super().form_valid(form)

class DepartmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Department
    template_name = 'hr/employee/department_form.html'
    fields = ['department_name', 'manager', 'location']  
    context_object_name = 'department'
    success_url = reverse_lazy('department-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Department'
        return context  

    def form_valid(self, form):
        # Any additional logic before saving can be added here
        messages.success(self.request, f'Deparment  [{form.instance.department_name}] updated successfully.')
        return super().form_valid(form)   

@login_required
def delete_department(request, pk):
    dept = Department.objects.get(id=pk)

    if request.method == "POST":
        dept.delete()
        messages.success(request, f"{dept} successfully deleted")
        return redirect('department-list')
    
    return render(request, 'core/delete.html', {'obj':dept, 'title': f'Delete {dept}?'})

# Job Views

class JobListView(LoginRequiredMixin, ListView):
    model = Job
    template_name = 'hr/employee/job_list.html'
    context_object_name = 'job_list'

    def get_queryset(self):
       queryset = super().get_queryset()
       queryset = queryset.order_by('created_at')
       return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Jobs'
        return context  

class JobCreateView(LoginRequiredMixin, CreateView):
    model = Job
    template_name = 'hr/employee/job_form.html'
    fields = ['job_title', 'min_salary', 'max_salary', 'currency']  
    success_url = reverse_lazy('job-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Job'
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Job {form.instance.job_title} was created successfully")
        return super().form_valid(form)

class JobUpdateView(LoginRequiredMixin, UpdateView):
    model = Job
    template_name = 'hr/employee/job_form.html'
    fields = ['job_title', 'min_salary', 'max_salary', 'currency']
    success_url = reverse_lazy('job-list')

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        context['title'] = 'Update Job'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, f"Job {form.instance.job_title} was updated successfully")
        return super().form_valid(form)
    
def delete_job(request, pk):
    job = Job.objects.get(id=pk)

    if request.method == "POST":
        job.delete()
        messages.success(request, f"{job} was deleted successfully")
        return redirect('job-list')

    return render(request, 'core/delete.html', {'obj':job, 'title': f'Delete {job}?'})
  
  # Job History

class JobHistoryListView(LoginRequiredMixin, ListView):
    model = JobHistory
    template_name = 'hr/employee/jhistory_list.html'
    context_object_name = 'job_history_list'

    def get_queryset(self):
       queryset = super().get_queryset()
       queryset = queryset.order_by('created_at')
       return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Job Histories'
        return context  

class JobHistoryCreateView(LoginRequiredMixin, CreateView):
    model = JobHistory
    form_class = JobHistoryForm
    template_name = 'hr/employee/jhistory_form.html'
    success_url = reverse_lazy('job-history-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Job History'
        return context

    def form_valid(self, form):
        messages.success(self.request, f"{form.instance.employee} job history was created successfully")
        return super().form_valid(form)

class JobHistoryUpdateView(LoginRequiredMixin, UpdateView):
    model = JobHistory
    form_class = JobHistoryForm
    template_name = 'hr/employee/jhistory_form.html'
    success_url = reverse_lazy('job-history-list')
    context_object_name = 'job_history'

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(self, **kwargs)
        context['title'] = 'Update Job History'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, f"{form.instance.employee} was updated successfully")
        return super().form_valid(form)
    
def delete_job_history(request, pk):
    jhistory = JobHistory.objects.get(id=pk)

    if request.method == "POST":
        jhistory.delete()
        messages.success(request, f"{jhistory} was deleted successfully")
        return redirect('job-history-list')

    return render(request, 'core/delete.html', {'obj':jhistory, 'title': f'Delete {jhistory}?'})
  
  # Employee
class EmployeeListView(LoginRequiredMixin, ListView):
    model = Employee
    template_name = 'hr/employee/employee_list.html'
    context_object_name =  'employee_list'

    def get_queryset(self):
       queryset = super().get_queryset()
       queryset = queryset.order_by('created_at')
       return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Employees'
        return context  

class EmployeeCreateView(LoginRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'hr/employee/employee_form.html'
    success_url = reverse_lazy('employee-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Employee'
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Employee [{form.instance.first_name} {form.instance.last_name}] was created successfully")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        # Add an error message to be displayed when the form is invalid
        messages.error(self.request, 'There was an error in the form. Please correct it and try again.')
        return self.render_to_response(self.get_context_data(form=form))

class EmployeeUpdateView(LoginRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'hr/employee/employee_form.html'
    success_url = reverse_lazy('employee-list')
    context_object_name = 'employee'

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        context['title'] = 'Update Employee'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, f"{form.instance.first_name} {form.instance.last_name} was updated successfully")
        return super().form_valid(form)
    
def delete_employee(request, pk):
    employee = Employee.objects.get(id=pk)

    if request.method == "POST":
        employee.delete()
        messages.success(request, f"{employee} was deleted successfully")
        return redirect('job-history-list')

    return render(request, 'core/delete.html', {'obj':employee, 'title': f'Delete {employee}?'})
 
class EmployeePhotoUpdateView(LoginRequiredMixin, UpdateView):
    model = Employee  # Ensure this is defined
    template_name = 'hr/employee/photo_form.html'
    fields = ['photo']
    success_url = reverse_lazy('employee-list')
    context_object_name = 'employee'

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        context['title'] = f'Upload Photo for {self.object}'
        return context
    
    def get_form(self, *args, **kwargs):
        form =  super(EmployeePhotoUpdateView, self).get_form(*args, **kwargs)
        form.fields['photo'].widget = forms.FileInput(attrs={'type':'file'})

        return form

    def form_valid(self, form):
        messages.success(self.request, f"{self.object} photo was uploaded successfully")
        return super().form_valid(form)
