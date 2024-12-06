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
from ..forms.employee_forms import JobHistoryForm, EmployeeForm, GuarantorForm, DocumentUploadForm, SMSForm, JobForm
from django.forms import modelformset_factory
import pdb
from django.db.models import Count
from django.db import transaction, IntegrityError, DatabaseError
from django.utils.safestring import mark_safe
import json


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

class DepartmentEmployeeDetailView(LoginRequiredMixin, DetailView):
    model = Department
    template_name = 'hr/generic/item_detail.html'
    context_object_name = 'department'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Employees in {self.get_object().department_name} "
        context['item'] = 'department'
        context['employees'] = Employee.objects.filter(job__department=self.get_object())
        return context

# Designations Views
class DesignationListView(LoginRequiredMixin, ListView):
    model = Designation
    template_name = 'hr/employee/designation_list.html'
    context_object_name = 'designation_list'

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        context['title'] = 'Designations'
        # get distinct level for filters
        context['level_list'] = Designation.objects.values('level').distinct()
        return context

class DesignationCreateView(LoginRequiredMixin, CreateView):
    model = Designation
    template_name = 'hr/employee/designation_form.html'
    fields = ['code', 'title', 'level']  
    success_url = reverse_lazy('designation-list')  
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Designation'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, f'Designation [{form.instance.title}] created successfully.')
        return super().form_valid(form)

class DesignationUpdateView(LoginRequiredMixin, UpdateView):
    model = Designation
    template_name = 'hr/employee/designation_form.html'
    fields = ['code', 'title', 'level']  
    context_object_name = 'designation'
    success_url = reverse_lazy('designation-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Update Designation ({self.get_object().title })"
        return context  

    def form_valid(self, form):
        # Any additional logic before saving can be added here
        messages.success(self.request, f'Designation  [{form.instance.title}] updated successfully.')
        return super().form_valid(form)  

@login_required
def delete_designation(request, pk):
    designation = Designation.objects.get(id=pk)

    if request.method == "POST":
        designation.delete()
        messages.success(request, f"{designation} successfully deleted")
        return redirect('designation-list')
    
    return render(request, 'core/delete.html', {'obj':designation, 'title': f'Delete {designation}?'})

class DesignationEmployeeDetailView(LoginRequiredMixin, DetailView):
    model = Designation
    template_name = 'hr/generic/item_detail.html'
    context_object_name = 'designation'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Employees holding {self.get_object().title} "
        context['item'] = 'designation'
        context['employees'] = Employee.objects.filter(designation=self.get_object())
        return context

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
        context['departments'] = Department.objects.filter(jobs__isnull=False).distinct()
        return context  

class JobCreateView(LoginRequiredMixin, CreateView):
    model = Job
    template_name = 'hr/employee/job_form.html'
    form_class = JobForm
    success_url = reverse_lazy('job-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Job'
        # Group skills by category for rendering in template
        skills_by_category = Skill.objects.values('category').annotate(skill_count=Count('id')).order_by('category')
        categorized_skills = {
            category['category']: Skill.objects.filter(category=category['category']) 
            for category in skills_by_category
        }
        context['categorized_skills'] = categorized_skills
        context['use_quill'] = True

        return context

    def form_valid(self, form):
        messages.success(self.request, f"Job {form.instance.job_title} was created successfully")
        return super().form_valid(form)

class JobUpdateView(LoginRequiredMixin, UpdateView):
    model = Job
    template_name = 'hr/employee/job_form.html'
    form_class = JobForm
    success_url = reverse_lazy('job-list')

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        context['title'] = f"Update Job ({self.get_object().job_title})"
        # Group skills by category for rendering in template
        skills_by_category = Skill.objects.values('category').annotate(skill_count=Count('id')).order_by('category')
        categorized_skills = {
            category['category']: Skill.objects.filter(category=category['category']) 
            for category in skills_by_category
        }
        context['categorized_skills'] = categorized_skills
        context['use_quill'] = True
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

class JobEmployeeDetailView(LoginRequiredMixin, DetailView):
    model = Job
    template_name = 'hr/generic/item_detail.html'
    context_object_name = 'job'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"{self.get_object().job_title} Employees"
        context['item'] = 'job'
        context['employees'] = Employee.objects.filter(job=self.get_object())
        context['use_quill'] = True
  
        return context


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
        context['designations'] = Designation.objects.filter(job_history__isnull=False).distinct()
        context['jobs'] = Job.objects.filter(job_history__isnull=False).distinct()
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title':'Employees',
            'id_list': NationalIDType.objects.all(),
            'designation_list':Designation.objects.all(),
            'department_list':Department.objects.all(),
            'salary_grade_list':SalaryGrade.objects.all(),
            'bank_list':Bank.objects.all(),
            'status_list':Employee.Status.choices
        })
        
        return context  
 
class EmployeeCreateView(LoginRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'hr/employee/employee_form.html'
    success_url = reverse_lazy('employee-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Employee'

        # Group skills by category for rendering in template
        skills_by_category = Skill.objects.values('category').annotate(skill_count=Count('id')).order_by('category')
        categorized_skills = {
            category['category']: Skill.objects.filter(category=category['category']) 
            for category in skills_by_category
        }
        context['selected_skills'] =  self.request.POST.getlist('skills') if self.request.method == "POST" else []
        context['categorized_skills'] = categorized_skills

        if self.request.POST:
            context['guarantor_form'] = GuarantorForm(self.request.POST)
        else:
            context['guarantor_form'] = GuarantorForm()
        return context
    # create leave balances for this employ
    def create_leave_balances(self, employee):
        leave_types = LeaveType.objects.all()
        for leave_type in leave_types:
            LeaveBalance.objects.create(
                employee=employee,
                leave_type=leave_type,
                used_days=0.0,
                accrued_days=0.0 if leave_type.method == 'accrual' else leave_type.entitlement
            )

    def form_valid(self, form):
        context = self.get_context_data()
        guarantor_form = context['guarantor_form']

        if form.is_valid() and guarantor_form.is_valid():
            with transaction.atomic():
                employee = form.save()

                # save the guarantor with a reference to the employe
                guarantor = guarantor_form.save(commit=False)
                guarantor.employee = employee
                guarantor.save()
            
                # create job history for the new employee
                JobHistory.objects.create(
                    employee=employee,
                    job=employee.job,
                    designation=employee.designation,
                    start_date=employee.hire_date
                )
                self.create_leave_balances(employee)

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
        employee = self.get_object()
        
        # retrieve skills and send to the template as selected_skills if job was selected and skills was selected during form creation
        selected_skills = []

        if self.request.POST:
            context['guarantor_form'] = GuarantorForm(self.request.POST, instance=self.get_first_guarantor())
            selected_skills = self.request.POST.getlist('skills') or []
        else:
            context['guarantor_form'] = GuarantorForm(instance=self.get_first_guarantor())
            if employee.job and employee.skills.exists():
                selected_skills =  [{'id':skill.id, 'name': skill.name} for skill in employee.skills.all()]
        context['selected_skills'] = selected_skills
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

# SMS


# SMS
class SMSListView(LoginRequiredMixin, ListView):
    model = SMS 
    template_name = 'hr/meeting/sms_list.html'
    context_object_name = 'sms_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'SMS'
        return context

class SMSCreateView(LoginRequiredMixin, CreateView):
    model = SMS 
    form_class = SMSForm
    template_name = 'hr/meeting/sms_form.html'
    success_url = reverse_lazy('sms-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Schedule New SMS'
        return context

    def form_valid(self, form):
        sms = form.save(commit=False)
        sms.save()
        form.save_m2m() # Save to the many to many models

        messages.success(self.request, f"SMS successfully scheduled")
        return super().form_valid(form)
    
class SMSUpdateView(LoginRequiredMixin, UpdateView):
    model = SMS
    form_class = SMSForm
    template_name = 'hr/meeting/sms_form.html'
    context_object_name = 'sms'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Update SMS {self.get_object().message[:20]}..."
        return context
    
    def form_valid(self, form):
       sms = form.save(commit=False)
       sms.save()
       form.save_m2m()

       messages.success(self.request, "Message successfully updated")
       return super().form_valid(form)

def delete_sms(request, pk):
    sms = SMS.objects.get(id=pk)

    if request.method == "POST":
        sms.delete()
        messages.success(request, f"{sms.message[:20]}... successfully deleted")
    return render(request, 'core/delete.html', context={'obj':sms, 'title':f"Delete {sms.message[:20]}...?"})

class SMSDetailView(LoginRequiredMixin, DetailView):
    model = SMS
    context_object_name = 'sms'
    template_name  = 'hr/meeting/sms_detail.html'

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)    
        sms = self.get_object()  
        context['title'] = f"{sms}"

        # get the list of employees who are affected by this sms
        context['employees'] = sms.get_sms_employees()
        return context
