from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from hr.models.payroll import *
from hr.models.employee import Employee
from django.db import transaction, DatabaseError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from ..forms.payroll_forms import SalaryItemForm

from hr.models.payroll import SalaryGrade
from .utils import compute_factor

class SalaryGradeListView(LoginRequiredMixin, ListView):
    model = SalaryGrade
    template_name = 'hr/payroll/salarygrade_list.html'
    context_object_name = 'salarygrade_list'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.order_by('created_at')

        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Salary Grades'
        return context


class SalaryGradeCreateView(LoginRequiredMixin, CreateView):
    model = SalaryGrade
    template_name = 'hr/payroll/salarygrade_form.html'
    fields = ['grade', 'grade_step', 'amount', 'currency']  
    success_url = reverse_lazy('salarygrade-list')  

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Salary Grade'
        return context

    
    def form_valid(self, form):
        messages.success(self.request, f'Salary grade [{form.instance.grade}] created successfully.')
        return super().form_valid(form)
    
class SalaryGradeUpdateView(LoginRequiredMixin, UpdateView):
    model = SalaryGrade
    template_name = 'hr/payroll/salarygrade_form.html'  
    fields = ['grade', 'grade_step', 'amount', 'currency']  
    context_object_name = 'salary_grade'
    success_url = reverse_lazy('salarygrade-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Salary Grade'
        return context  

    def form_valid(self, form):
        # Any additional logic before saving can be added here
        messages.success(self.request, f'Salary grade [{form.instance.grade}] updated successfully.')
        return super().form_valid(form)
 
@login_required
def delete_salary_grade(request, pk):
    grade = SalaryGrade.objects.get(id=pk)

    if request.method == "POST":
        grade.delete()
        messages.success(request, f"{grade} successfully deleted")
        return redirect('salarygrade-list')
    
    return render(request, 'core/delete.html', {'obj':grade, 'title': f'Delete {grade}?'})

class SalaryGradeEmployeeDetailView(LoginRequiredMixin, DetailView):
    model = SalaryGrade
    template_name = 'hr/generic/item_detail.html'
    context_object_name = 'salary_grade'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"{self.get_object().grade} Employees"
        context['item'] = 'salary_grade'
        context['employees'] = Employee.objects.filter(salary_grade=self.get_object())
        
        return context   

# Tax Setup

def setup_tax(request):
    context = {'title':'Tax Setup'}

    if request.method == "POST":
        with transaction.atomic():
        
            # clear the existence tax block for the current year if exist..
            current_year = timezone.now().year
            Tax.objects.filter(year=current_year).delete()
            
            existing_tax_blocks = Tax.objects.filter(year=timezone.now().year)
            if existing_tax_blocks:
                existing_tax_blocks.delete()
            
            # Get blocks and rates from the POST data
            blocks = request.POST.getlist('block[]')
            rates = request.POST.getlist('rate[]')
            errors = []

            tax_entries = []
            previous_rate = None

            try:
                for i in range(len(blocks)):
                    # We convert block and rate to float
                    block_amount = float(blocks[i]) if blocks[i] else None
                    rate_percent = float(rates[i]) if rates[i] else None

                    # Validate rate and ensure they ascend in order
                    # Skip the first block since rate is mostly 0 or 0
                    if i > 0 and previous_rate is not None and rate_percent < previous_rate:
                        errors.append(f"Rate for block {i + 1} must be higher than the previous block.")
        
                    previous_rate = rate_percent  # Update previous_rate for the next iteration
                    # Create tax instance and save later at once..
                    tax_entries.append(Tax(year=current_year, block=block_amount, rate=rate_percent))

                if errors:
                    return JsonResponse({'status':'fail', 'message':"<br>".join([error for error in errors])})
                
                # Create the tax entries now
                Tax.objects.bulk_create(tax_entries)
                return JsonResponse({'status': 'success', 'message': f"Tax setup successfully updated for the current year({current_year})"})


            except ValueError as e:
                # If any conversion fails, return an error response
                return JsonResponse({'status': 'fail', 'message': 'Invalid input. Please ensure all values are numbers.'})

    return render(request, 'hr/payroll/setup_tax.html', context)

# Salary Items
class SalaryItemListView(LoginRequiredMixin, ListView):
    model = SalaryItem
    template_name = 'hr/payroll/salaryitem_list.html'
    context_object_name = 'salaryitem_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Salary Items'
        return context

class SalaryItemCreateView(LoginRequiredMixin, CreateView):
    model = SalaryItem
    template_name = "hr/payroll/salaryitem_form.html"
    form_class = SalaryItemForm
    # success_url = reverse_lazy('salaryitem-list')

    def get_success_url(self):
        salary_item = self.object   
        if salary_item.rate_type == 'variable':
            return reverse_lazy('salaryitem-variable', kwargs={'pk':salary_item.id})
        else:
            return reverse_lazy('salaryitem-employee', kwargs={'pk':salary_item.id})
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Salary Item'
        context['rate_type'] = self.request.POST.get('rate_type') if self.request.method == "POST" else 'fix'
        context['rate_dependency'] = self.request.POST.get('rate_dependency') or '' 
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)

        # retrieve created salary item and set amount for affected employees
        salary_item = form.instance

        # retrieve filtered employees
        employees = salary_item.get_eligible_employees()

        # We create staff salary item for each employee with this salary item
        with transaction.atomic():
            for employee in employees:
                # Deduce actual amount based on 'rate' of 'type' fix or factor
                # for fix rate, the rate amount is used
                # for factor, (rate amount / 100) * Basic or another salary item (rate amount)
                rate_type = salary_item.rate_type
                if rate_type == 'fix':
                    amount = salary_item.rate_amount
                elif rate_type == 'factor':
                    amount = compute_factor(employee, salary_item.rate_amount, salary_item.rate_dependency)
                else:
                    # for variable, set the default amount to 0
                    amount = 0
                StaffSalaryItem.objects.create(
                    salary_item=salary_item,
                    employee=employee,
                    amount=amount,
                )

        messages.success(self.request, f"Salary item [{form.instance.item_name}] successfully created and applied to { employees.count() } employee(s)")
       
        self.object.update_eligible_employee_count()
        return redirect(self.get_success_url())
        
        # return response

class SalaryItemUpdateView(LoginRequiredMixin, UpdateView):
    model = SalaryItem
    form_class = SalaryItemForm
    template_name = 'hr/payroll/salaryitem_form.html'
    context_object_name = 'salary_item'

    def get_success_url(self):
        salary_item = self.object
        
        if salary_item.rate_type == 'variable':
            return reverse_lazy('salaryitem-variable', kwargs={'pk':salary_item.id})
        else:
            return reverse_lazy('salaryitem-employee', kwargs={'pk':salary_item.id})
    
    def get_context_data(self, **kwargs):
        salary_item = self.get_object()
        context =  super().get_context_data(**kwargs)
        context['title'] = f"Update {salary_item.item_name}"
        context['rate_type'] = self.request.POST.get('rate_type') if self.request.method == "POST" else salary_item.rate_type
        context['rate_dependency'] = self.request.POST.get('rate_dependency') or salary_item.rate_dependency 
        context['real_old_employees'] = salary_item.get_eligible_employees()
        return context
    

    def form_valid(self, form):
        # Retrieve the previous instance before saving changes to get old state of eligible employees (will be used later for accurate comparision of new state of employee)
        old_instance = self.get_object()
        old_employees = set(old_instance.get_eligible_employees())

        with transaction.atomic():

            new_instance = form.save() #commit=False
 
            # Fetch eligible employees for new instanace after saving

            new_employees = set(new_instance.get_eligible_employees())

            # Deduce employees states to add or delete
            employees_to_add = new_employees - old_employees
            employees_to_remove = old_employees - new_employees
     

            # Update amount for existig employees
            if (old_instance.rate_type != new_instance.rate_type or
                old_instance.rate_amount != new_instance.rate_amount or
                old_instance.rate_dependency != new_instance.rate_dependency):

                for staff_salary in StaffSalaryItem.objects.filter(salary_item=old_instance, employee__in=old_employees):
                    if new_instance.rate_type == 'fix':
                        # set amount directly
                        staff_salary.amount = new_instance.rate_amount
                        # reset variable if there is a transition
                        if old_instance.rate_type == 'variable':
                            staff_salary.variable = 0

                    elif new_instance.rate_type == 'factor':
                        # compute amount based on dependency and rate
                        staff_salary.amount = compute_factor(staff_salary.employee, new_instance.rate_amount, new_instance.rate_dependency)
                    elif new_instance.rate_type == 'variable':
                        # if transition is from 'non variable' to variable, set the amount if previous variable exist or 0 for later updates..
                        staff_salary.amount = staff_salary.variable * new_instance.rate_amount  if staff_salary.variable else 0
                    staff_salary.save()

            # Remove staff salary items for employees no longer eligible
            StaffSalaryItem.objects.filter(salary_item=old_instance, employee__in=employees_to_remove).delete()

            # Add staff salary items for newly eligible employees
            for employee in employees_to_add:
                if new_instance.rate_type == 'fix':
                    amount = new_instance.rate_amount
                elif new_instance.rate_type == 'factor':
                    amount = compute_factor(employee, new_instance.rate_amount, new_instance.rate_dependency)
                else:
                    # Variable rate type; initialize amount as 0, allowing future updates per employee
                    amount = 0
                
                StaffSalaryItem.objects.create(
                    salary_item=new_instance,
                    employee=employee,
                    amount=amount
                )
            # form.save_m2m()
            messages.success(self.request, f"Salary item [{form.instance.item_name}] successfully updated and applied to { len(new_employees) } employee(s)")

            self.object.update_eligible_employee_count()
            return redirect(self.get_success_url())    
            # return super().form_valid(form)
    
    
def delete_salary_item(request, pk):
    salary_item = SalaryItem.objects.get(id=pk)

    if request.method == "POST":
        salary_item.delete()
        messages.success(request, f"{salary_item} successfully deleted")
        return redirect('salaryitem-list')
    
    return render(request, 'core/delete.html', {'obj':salary_item, 'title': f'Delete {salary_item}?'})

class SalaryItemEmployeeDetailView(LoginRequiredMixin, DetailView):
    model = SalaryItem
    template_name = 'hr/payroll/salaryitem_employee_detail.html'
    context_object_name = 'salary_item'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        salary_item = self.get_object()
        context['title'] = f"{salary_item.item_name} Employees"
        # check the update and create salary item script to ensure integrity, if it fails, then get the list of employee from staff salary item and manually filter out using get_eligible_employees..
        
        # when rate type is factor and 'Basic' wasn't selected, retrieve the actual salary item name through the supplied id
        if salary_item.rate_type == 'factor':
            dependency = "Basic Salary"
            if salary_item.rate_dependency !=  "Basic":
                try:
                    dependency = SalaryItem.objects.get(id=salary_item.rate_dependency).item_name
                except ValueError as e:
                    dependency = 'Unknown Item'
            
            context['dependency'] = dependency

        context['employees'] = StaffSalaryItem.objects.filter(salary_item=salary_item)
        return context

class SalaryItemVariableDetailView(LoginRequiredMixin, DetailView):
    model = SalaryItem
    template_name = 'hr/payroll/salaryitem_variable_detail.html'
    context_object_name = 'salary_item'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        salary_item = self.get_object()
        context['title'] = f"{salary_item.item_name} Employees Variable Set"
        context['employees'] = StaffSalaryItem.objects.filter(salary_item=salary_item)
        return context

    def get_success_url(self):
        id = self.get_object().id
        return reverse_lazy('salaryitem-employee', kwargs={'pk':id})
 
    def post(self, request, *args, **kwargs):
        # print(self.request.POST)
        salary_item = self.get_object()

        if self.request.method == "POST":
            with transaction.atomic():
                for item in StaffSalaryItem.objects.filter(salary_item=salary_item):
                    variable_key = f"variable_{item.id}"
                    variable = self.request.POST.get(variable_key)

                    try:
                      if variable:
                        amount = int(salary_item.rate_amount) * int(variable)
                        item.amount = amount
                        item.variable = variable
                        item.save()                  
                    except DatabaseError as e:
                        messages.error(self.request, "An error occured while updating employees variable, try again later")

                
                messages.success(self.request, f"{salary_item.item_name} employee(s) variable updated successfully")
                return redirect(self.get_success_url()) #self.form_valid(form)
