from django.db.models.query import QuerySet
from django.forms import BaseModelForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.views.generic.edit import FormMixin

from hr.models.employee import *
from django.urls import reverse_lazy
from django import forms
from ..forms.employee_forms import JobHistoryForm, EmployeeForm, GuarantorForm, DocumentUploadForm
from django.forms import modelformset_factory
import pdb
from django.db.models import Count


# Create your views here.
class DepartmentListView(LoginRequiredMixin, ListView):
    model = Department
    template_name = 'hr/employee/department_list.html'
    context_object_name = 'department_list'

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
       queryset = queryset.annotate(
           employee_count=Count('employees')
       )
       return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Jobs'
        return context  

class JobCreateView(LoginRequiredMixin, CreateView):
    model = Job
    template_name = 'hr/employee/job_form.html'
    fields = ['job_title', 'department', 'min_salary', 'max_salary', 'currency']  
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
    fields = ['job_title', 'department', 'min_salary', 'max_salary', 'currency']
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

    # def get_queryset(self):
    #    queryset = super().get_queryset()
    #    queryset = queryset.order_by('created_at')
    #    return queryset

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
        if self.request.POST:
            context['guarantor_form'] = GuarantorForm(self.request.POST)
        else:
            context['guarantor_form'] = GuarantorForm()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        guarantor_form = context['guarantor_form']

        if form.is_valid() and guarantor_form.is_valid():
            employee = form.save()

            # save the guarantor with a reference to the employe
            guarantor = guarantor_form.save(commit=False)
            guarantor.employee = employee
            guarantor.save()
           
            # create job history for the new employee
            JobHistory.objects.create(
                employee=employee,
                job=employee.job,
                start_date=employee.hire_date
            )
            
            messages.success(self.request, f"Employee [{form.instance.first_name} {form.instance.last_name}] was created successfully")
            return super().form_valid(form)
        else:
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        messages.error(self.request, 'There was an error in the form. Please correct it and try again.')
        
        # we include the GuarantorFormSet in the context when the form is invalid
        context['guarantor_form'] = GuarantorForm(self.request.POST)
        return self.render_to_response(context)

class EmployeeUpdateView(LoginRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'hr/employee/employee_form.html'
    success_url = reverse_lazy('employee-list')
    context_object_name = 'employee'

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        context['title'] = 'Update Employee'

        if self.request.POST:
            context['guarantor_form'] = GuarantorForm(self.request.POST, instance=self.get_first_guarantor())
        else:
            context['guarantor_form'] = GuarantorForm(instance=self.get_first_guarantor())
        return context
    
    def get_first_guarantor(self):
        """ Helper method to get the first guarantor for this employee"""
        try:
            return self.object.guarantors.first()
        except Guarantor.DoesNotExist:
            return None
    
    def form_valid(self, form):
        context = self.get_context_data()
        guarantor_form = context['guarantor_form']

        if form.is_valid() and guarantor_form.is_valid():
            employee = form.save()

            guarantor = guarantor_form.save(commit=False)
            guarantor.employee = employee
            guarantor.save()

            messages.success(self.request, f"{form.instance.first_name} {form.instance.last_name} was updated successfully")
            return super().form_valid(form)
        else:
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        messages.error(self.request, 'There was an error in the form. Please correct it and try again.')
        
        return self.render_to_response(context)

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

class EmployeeDocumentView(LoginRequiredMixin, FormMixin, DetailView):
    model = Employee
    template_name = 'hr/employee/employee_documents.html'
    context_object_name = 'employee'
    form_class = DocumentUploadForm

    def get_success_url(self):
        return reverse_lazy('employee-file-upload', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        context['documents'] = Document.objects.filter(employee=self.get_object())
        context['title'] = f"Documents for {self.get_object()}"
        return context
    
    def post(self, request, *args, **kwargs):
        """Handles document upload"""
        self.object = self.get_object()
        form = self.get_form()
        # print(f"Document employee {employee}")

        if form.is_valid():
            document = form.save(commit=False)
            document.employee = self.object
           # print(f'debug form.is_valid() {employee}')
            if not document.document_type.allow_multiple:
                existing_docs = Document.objects.filter(employee=self.object, document_type=document.document_type)
                if existing_docs.exists():
                    form.add_error('document_type', f"Employee already has a {document.document_type.name} document. Only one is allowed.")
                    return self.form_invalid(form)
            document.save()
            messages.success(self.request, 'Document uploaded successfully.')
            return redirect(self.get_success_url()) #self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Handles invalid form submission"""
        context = self.get_context_data(form=form)
        messages.error(self.request, "Error: Document could not be uploaded. Please fix the errors below.")
        return self.render_to_response(context)
    
class EmployeeDetailView(LoginRequiredMixin, DetailView):
    model = Employee
    template_name = 'hr/employee/employee_detail.html'
    context_object_name = 'employee'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'{self.get_object()} Profile'
        context['guarantors'] = Guarantor.objects.filter(employee=self.get_object())
        context['histories'] = JobHistory.objects.filter(employee=self.get_object()).order_by('created_at')
        context['documents'] = Document.objects.filter(employee=self.get_object())
        return context
    