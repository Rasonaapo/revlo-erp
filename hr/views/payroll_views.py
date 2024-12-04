from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from hr.models.payroll import *
from hr.models.employee import Employee
from django.db import transaction, DatabaseError, IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from ..forms.payroll_forms import SalaryItemForm, LoanForm, CreditUnionForm, PayrollForm
from django.db.models import Q, Prefetch, Sum, Count
from hr.models.payroll import SalaryGrade, Tax
from .utils import compute_factor, get_filtered_staff_credit_union, get_filtered_staff_payroll
from decimal import Decimal
import logging
from pprint import pprint

logger = logging.getLogger(__name__)


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
@login_required
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
        with transaction.atomic():
            try:
                # retrieve created salary item and set amount for affected employees
                salary_item = form.save()
                self.object = salary_item
                # retrieve filtered employees
                employees = salary_item.get_eligible_employees()
                if employees.count() == 0:
                    form.add_error(None, "Selected filter(s) did not affect any employee. Please rectify and proceed")
                    salary_item.delete()
                    return self.form_invalid(form)

                print(salary_item.rate_type)

                # We create staff salary item for each employee with this salary item
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
            
                salary_item.update_eligible_employee_count()
                return redirect(self.get_success_url())

            except IntegrityError:
                form.add_error(None, "An error occured while saving Salary Item. Please try again")
                return self.form_invalid(form)
          
        

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
            try:
                new_instance = form.save() #commit=False
                # Fetch eligible employees for new instanace after saving

                new_employees = set(new_instance.get_eligible_employees())

                #Ensure filter(s) returns at least one employee for this salary item
                if len(new_employees) == 0:
                    form.add_error(None, "Selected filter(s) did not affect any employee. Please rectify and proceed")
                    return self.form_invalid(form)

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

            except IntegrityError:
                form.add_error(None, "An error occured while saving Salary Item. Please try again")
                return self.form_invalid(form)

@login_required  
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

# Loan

class LoanListView(LoginRequiredMixin, ListView):
    model = Loan
    template_name = 'hr/payroll/loan_list.html'
    context_object_name = 'loan_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Loans"

        # get distinct status for filtering purposes
        statuses = Loan.objects.all().values_list('status', flat=True).distinct()
        context['status_labels'] = [(value, dict(Loan.LoanStatus.choices).get(value,value)) for value in statuses]

        loan_types = Loan.objects.all().values_list('loan_type', flat=True).distinct()
        context['loan_types'] = [(value, dict(Loan.LoanType.choices).get(value,value)) for value in loan_types]
        
        return context
    
class LoanCreateView(LoginRequiredMixin, CreateView):
    model = Loan
    form_class = LoanForm
    template_name = 'hr/payroll/loan_form.html'
    success_url = reverse_lazy('loan-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Add Loan"
        return context
    
    def form_valid(self, form):
        loan = form.save()
        messages.success(self.request, f"{loan.get_loan_type_display()} for {loan.employee.first_name} successfully created")
        return super().form_valid(form)

class LoanUpdateView(LoginRequiredMixin, UpdateView):
    model = Loan
    template_name = 'hr/payroll/loan_form.html'
    form_class = LoanForm
    success_url = reverse_lazy('loan-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Update {self.get_object()}"
        return context
    
    def form_valid(self, form):

        messages.success(self.request, f"{self.get_object()} successfully updated")
        return super().form_valid(form)
    
class LoanDeleteView(LoginRequiredMixin, DeleteView):
    model = Loan
    template_name = 'core/delete.html'
    success_url = reverse_lazy('loan-list')
    success_message = "%(loan_type)s for %(employee)s successfully deleted."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        loan = self.get_object()
        context['obj'] = loan
        context['title'] = f"Delete {loan}"
        return context
    
    def delete(self, request, *args, **kwargs):
        """
        Override delete method to add a success message.
        """
        loan = self.get_object()
        messages.success(request, f"Loan for {loan.employee} successfully deleted.")
        return super().delete(request, *args, **kwargs)
    
class LoanDetailView(LoginRequiredMixin, DetailView):
    model = Loan
    template_name = 'hr/payroll/loan_detail.html'
    context_object_name = 'loan'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        loan = self.get_object()
        context["title"] = f"{loan}" 
                # Load repayment records for this loan
        context['loan_repayments'] = LoanRepayment.objects.filter(loan=loan)

        return context
    
# Credit Union

class CreditUnionListView(LoginRequiredMixin, ListView):
    model = CreditUnion
    template_name = 'hr/payroll/creditunion_list.html'
    context_object_name = 'credit_union_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Credit Unions"
        return context

class CreditUnionCreateView(LoginRequiredMixin, CreateView):
    model = CreditUnion
    form_class = CreditUnionForm
    template_name = 'hr/payroll/creditunion_form.html'
    success_url = reverse_lazy('creditunion-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Add Credit Union"
        return context
    
    def form_valid(self, form):
        with transaction.atomic():
            try:
                credit_union = form.save()

                # prepopulate staff credit union using default amount, start and end date if provided..
                default_amount = credit_union.amount or 0
                default_start_date = credit_union.deduction_start_date
                default_end_date = credit_union.deduction_end_date
                
                print(default_start_date)
                # credit_union.deduction_start_date=default_start_date
                # credit_union.save()

                if default_amount == 0:
                    messages.warning(self.request, f"No default amount set for {credit_union.union_name}, Please update individual staff records")

                # Retrieve eligible employees and create staff credit union records..
                eligible_employees = credit_union.get_eligible_employees()
                if eligible_employees.count() == 0:
                    form.add_error(None, "Selected filter did not affect any employee, kindly rectify to proceed")
                    credit_union.delete()
                    return self.form_invalid(form)
                
                batch_records = []
                
                for employee in eligible_employees:
                    batch_records.append(StaffCreditUnion(
                        credit_union=credit_union,
                        employee=employee,
                        amount=default_amount,
                        deduction_start_date=default_start_date,
                        deduction_end_date=default_end_date
                    ))
                
                # Create bulk records now
                StaffCreditUnion.objects.bulk_create(batch_records)
                messages.success(self.request, f"{credit_union} successfully created and applied to {eligible_employees.count()} employee(s)")  

                return  super().form_valid(form)
        
            except IntegrityError as e:
                print(e)
                form.add_error(None, "An error occured while saving Credit Union. Please try again")
                return self.form_invalid(form)
            
class CreditUnionUpdateView(LoginRequiredMixin, UpdateView):
    model = CreditUnion
    form_class = CreditUnionForm
    template_name = 'hr/payroll/creditunion_form.html'
    success_url = reverse_lazy('creditunion-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        credit_union = self.get_object()
        context['title'] = f"Update {credit_union}"
        return context

    def form_valid(self, form):
     # retrieve old instance and check cases where the default amount is updated, in such case, update it for all the members in this union
     old_instance = self.get_object()
     old_employees = set(old_instance.get_eligible_employees())
     cleaned_data = form.cleaned_data

     with transaction.atomic():
        try:
            form.save(commit=False) # Dont' commit yet..
            if form.errors:
                print("Form Errors:", form.errors)
                return self.form_invalid(form)
            print("Cleaned Data:", cleaned_data)            
            
            # use the synthetic util function to get supposed eligible employees
            synthetic_new_employees = set(get_filtered_staff_credit_union(cleaned_data['all_employee'], cleaned_data['department'], cleaned_data['applicable_to'], cleaned_data['excluded_from']))
            
            if len(synthetic_new_employees) == 0:
                form.add_error(None, "Your new filter(s) did not affect any employee, rectify to proceed")    
                return self.form_invalid(form)

            # Now commit to get actual employees
            new_instance = form.save()
            new_employees = set(new_instance.get_eligible_employees())

            # compute employees to be added to staff credit union
            employee_to_add = new_employees - old_employees
            employee_to_remove = old_employees - new_employees
            
            # Check for changes in the fields and update for existing staff credit union records
            if old_instance.amount != new_instance.amount: 
                # Admin intends to update only amount for all staff credit union members
                StaffCreditUnion.objects.filter(credit_union=new_instance).update(
                    amount=new_instance.amount
                )
            
            if old_instance.deduction_start_date != new_instance.deduction_start_date:
               print('Update start date')
               # Admin intends to update only deduction start date for all staff...
               StaffCreditUnion.objects.filter(credit_union=new_instance).update(deduction_start_date=new_instance.deduction_start_date)

            if old_instance.deduction_end_date != new_instance.deduction_end_date:
               print('Update end date')
               # Admin intends to update only deduction end date for all staff...
               StaffCreditUnion.objects.filter(credit_union=new_instance).update(deduction_end_date=new_instance.deduction_end_date)  

            # Create new staff to credit union if any
            if employee_to_add:
                new_records = [StaffCreditUnion(
                                    credit_union=new_instance,
                                    employee=employee,
                                    amount=new_instance.amount,
                                    deduction_start_date=new_instance.deduction_start_date,
                                    deduction_end_date=new_instance.deduction_end_date
                                ) 
                                for employee in employee_to_add 
                            ]
                StaffCreditUnion.objects.bulk_create(new_records)
            
            # delete unwanted staff from credit union if any
            if employee_to_remove:
                StaffCreditUnion.objects.filter(credit_union=new_instance, employee__in=employee_to_remove).delete()
            
            messages.success(self.request, f"{new_instance} successfully updated")

        except IntegrityError as e:
             print(e)
             form.add_error(None, "An error occured while updating Credit Union. Try again later")
             
     return  super().form_valid(form)

class CreditUnionDetailView(LoginRequiredMixin, DetailView):
    model = CreditUnion
    template_name = 'hr/generic/item_detail.html'
    context_object_name = 'credit_union'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        credit_union = self.get_object()
        context['title'] = f"{credit_union} Employees Details"
        context['item'] = "credit_union"
        context['staff_credit_unions'] = StaffCreditUnion.objects.filter(credit_union=credit_union)
        return context

@login_required
def delete_credit_union(request, pk):
    credit_union = CreditUnion.objects.get(id=pk)

    if request.method == "POST":
        credit_union.delete()
        messages.success(request, f"{credit_union} successfully deleted")
        return redirect('creditunion-list')

    return render(request, 'core/delete.html', {'obj':credit_union, 'title': f'Delete {credit_union}?'})

class CreditUnionSetEmployeeDetailView(LoginRequiredMixin, DetailView):
    model = CreditUnion
    template_name = "hr/payroll/creditunion_set_detail.html"
    context_object_name = "credit_union"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        credit_union = self.get_object()
        context['title'] = f"{credit_union} - Set Employees Details"
        context['staff_credit_unions'] = StaffCreditUnion.objects.filter(credit_union=credit_union)
      
        return context

    def post(self, request, *args, **kwargs):
         with transaction.atomic():
             try:
                amount_list = self.request.POST.getlist('amount[]')
                start_date_list = self.request.POST.getlist('start-date[]')
                end_date_list = self.request.POST.getlist('end-date[]')
                id_list = self.request.POST.getlist('id[]')  

                line = 1
                errors = []
                entries_to_update = []

                for i in range(len(amount_list)):
                    # retrieve individual records
                    amount = amount_list[i]
                    start_date = start_date_list[i]
                    end_date = end_date_list[i]
                    id = id_list[i]
                    staff_credit_union = StaffCreditUnion.objects.get(id=id)
                    # if start date and end date are supplied, ensure sanity. end date can not be earlier than start date
                    if end_date and start_date:
                        if end_date < start_date:
                           errors.append(f"End date can not be earlier than start date for {staff_credit_union.employee} on line {line}")
                        
                        if not amount:
                            errors.append(f"Amount can not be empty for {staff_credit_union.employee} on line {line}")

                    # if end date is specified, ensure that there is a corresponding start date
                    if not start_date and end_date:
                        errors.append(f"Start date must be set if an end date is specified for {staff_credit_union.employee} on line {line}")

                    # raise error for end date without start date and amount
                    if end_date and not start_date and not amount:
                        errors.append(f"Start date and or amount must be set if end date is specified for {staff_credit_union.employee} on line {line}")
                    
                    # Update the fields with relevant data
                    staff_credit_union.amount = amount or None
                    staff_credit_union.deduction_start_date = start_date or None
                    staff_credit_union.deduction_end_date = end_date or None

                    entries_to_update.append(staff_credit_union)
                        
                    line += 1
                
                if len(errors) > 0:
                    error_messages = "<br>".join([error for error in errors])
                    return JsonResponse({'errors': errors}, status=400)             
                # Perform bulk update
                StaffCreditUnion.objects.bulk_update(entries_to_update, ['amount', 'deduction_start_date', 'deduction_end_date'])

                return JsonResponse({"status":"success", "message":"Employees details successfully updated"})

             except DatabaseError:
                 return JsonResponse({'status':'error', 'message':'An error occured while processing record. Try again later'})

class PayrollCreateView(LoginRequiredMixin, CreateView):
    model = Payroll
    template_name = 'hr/payroll/process_payroll.html'
    form_class = PayrollForm
    success_url = reverse_lazy('process-payroll')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Process Payroll"
        return context

    def form_valid(self, form):
        # ensure atomicity
        cleaned_data = form.cleaned_data
        
        synthetic_employees = get_filtered_staff_payroll(cleaned_data)
        error_mode = cleaned_data['error_mode']

        with transaction.atomic():
            try:
                # commit the form to get the instance
                payroll_instance = form.save(commit=False)
                if form.errors:
                    errors = form.add_error
                    return JsonResponse({'errors':errors}, status=400)

                # retrieve filtered eligible employees and proceed with detailed processing of salary items, banks, loan etc
                if len(synthetic_employees) == 0:
                    return JsonResponse({'status':'fail', 'message':'Your selected filters did not match any employees. Please adjust and try again.'})

                # Begin payroll processing as we loop through synthetic employee
                bulk_entries = []; error_entries = []; errors = []; success_message = ''; invalid_employees = set()

                # Retrieve payment rate and use it on every amount
                payment_rate = cleaned_data['payment_rate']
                today = date.today()

                for employee in synthetic_employees:
                    staff_total_earnings = 0; staff_total_deductions = 0; total_credit = 0; total_debit = 0

                    # 1. Tax
                    if not employee.salary_grade:
                        errors.append(f"{employee}: Update salary grade details (grade/step/amount)")
                        # raise an error (set basic salary for grade salary_grade)
                        error_entries.append(PayrollError(employee=employee, payroll=payroll_instance, error_category='salary_grade'))
                        continue

                    salary_grade = employee.salary_grade
                    basic_salary = float(salary_grade.amount)
                    step = salary_grade.grade_step

                    # compute tax relief
                    tax_relief = employee.tax_relief or 0
                    if tax_relief > 0:
                        tax_relief = (payment_rate * tax_relief) / 100

                    # Check if employee has bank details
                    if not employee.bank: # or employee.bank.account == None: all in one check..
                        errors.append(f"{employee}: Update bank details (bank/account number/branch etc)")
                        # raise an error bank such as either employee has not bank information or bank is not link to chart of account code..
                        error_entries.append(PayrollError(employee=employee, payroll=payroll_instance, error_category='bank'))
                        continue

                    # compute for employee & employer ssnits
                    employer_ssnit = (basic_salary * 13) / 100
                    employee_ssnit = (basic_salary * 5.5) / 100

                    # get this employee salary items
                    staff_salary_items = StaffSalaryItem.objects.filter(Q(employee=employee) & Q(amount__gt=0) & (Q(salary_item__expires_on__isnull=True) | Q(salary_item__expires_on__gte=today)) )

                    # if there exists some records, then proceed
                    if staff_salary_items.exists():
                        for staff_item in staff_salary_items:
                            item_amount = float(staff_item.amount) #* payment_rate) / 100
                            
                            if staff_item.salary_item.effect == 'addition':
                                item_entry = 'debit' 
                                staff_total_earnings += item_amount
                                # total_debit += item_amount
                            else:
                                item_entry = 'credit'
                                staff_total_deductions += item_amount
                                # total_credit += item_amount

                            # save this item
                            bulk_entries.append(PayrollItem(payroll=payroll_instance, employee=employee, item_type='salary_item', dependency=staff_item.salary_item.id, amount=item_amount, entry=item_entry))

                    # get this employee credit unions deductions
                    staff_credit_unions = StaffCreditUnion.objects.filter(employee=employee, amount__isnull=False).filter(
                        Q(deduction_start_date__isnull=False,
                          deduction_end_date__isnull=True,
                          deduction_start_date__lte=today
                        ) |
                        Q(deduction_start_date__isnull=False,
                          deduction_end_date__isnull=False,
                          deduction_start_date__lte=today,
                          deduction_end_date__gte=today
                        )
                    )
                    # check for the existence of active credit unions
                    if staff_credit_unions.exists():
                        for staff_credit_union in staff_credit_unions:
                            monthly_deduction = staff_credit_union.amount

                            StaffCreditUnionDeduction.objects.create(staff_credit_union=staff_credit_union, amount_paid=monthly_deduction, date_paid=today)
                            # Add monthly deduction to total deduction
                            staff_total_deductions += monthly_deduction
                            # Save credit union
                            bulk_entries.append(PayrollItem(payroll=payroll_instance, employee=employee, item_type='credit_union', description=staff_credit_union.credit_union.union_name,  amount=monthly_deduction, dependency=staff_credit_union.credit_union.id,  entry='credit'))

                    # get employee loan(s)
                    staff_loans = Loan.objects.filter(employee=employee, status='active', outstanding_balance__gt=0, deduction_end_date__gt=today)
                    # if there are indeed active loans
                    if staff_loans.exists():
                        for loan in staff_loans:
                            outstanding_balance = loan.outstanding_balance
                            monthly_installment = loan.monthly_installment
                            """pay monthly installment if outstanding balance is greater else pay what it is left. This is because there is a posibility for employee to pay some using other means (like bank transfer/pay-in-slip) apart from payroll"""
                            
                            repayment_amount = min(monthly_installment, outstanding_balance)

                            # LoanRepayment.objects.create(loan=loan, amount_paid=repayment_amount)
                            # Call LoanRepayment in the finance app when PV is posted..

                            # add repayment amount total deduction
                            staff_total_deductions += repayment_amount
                            # save individual loan
                            bulk_entries.append(PayrollItem(payroll=payroll_instance, employee=employee, item_type='loan', description=loan.get_loan_type_display(),  amount=repayment_amount, dependency=loan.id,  entry='credit'))
                           
                            # total_credit += repayment_amount
                    # save earnings and deductions
                    bulk_entries.append(PayrollItem(payroll=payroll_instance, employee=employee, item_type='earning',  amount=staff_total_earnings,  entry='debit'))
                    
                    bulk_entries.append(PayrollItem(payroll=payroll_instance, employee=employee, item_type='deduction',  amount=staff_total_deductions,  entry='credit'))
                   
                    """add total staff earnings to basic salary which will be gross/taxable.."""
                    gross = (basic_salary + staff_total_earnings)
                    taxable = gross
                    # take out employee ssnit from taxable/basic
                    taxable -= employee_ssnit
                    # take out tax relief
                    taxable -= tax_relief

                    # Now compute for tax
                    income_tax = Tax.calculate_tax(payroll_instance.process_year, taxable)

                    # Add tax and employee ssnit to staff total deductions
                    staff_total_deductions = float(staff_total_deductions)
                    staff_total_deductions += (income_tax  + employee_ssnit)

                    # compute for net salary
                    net = gross - staff_total_deductions

                    total_debit = gross 
                    total_credit = net + staff_total_deductions
                    
                    #save net salary
                    bulk_entries.append(PayrollItem(payroll=payroll_instance, employee=employee, item_type='net_salary', amount=net, entry='credit'))
                    # save gross salary
                    bulk_entries.append(PayrollItem(payroll=payroll_instance, employee=employee, item_type='gross_salary', amount=gross, entry='credit'))
                    # save taxability
                    bulk_entries.append(PayrollItem(payroll=payroll_instance, employee=employee, item_type='taxability', amount=taxable, entry='credit'))
                   

                    # save bank 
                    bulk_entries.append(PayrollItem(payroll=payroll_instance, employee=employee, item_type='bank', amount=net, dependency=employee.bank.id, entry='credit'))
                    # Save payroll items which are not dynamically gotten from loop
                    # save basic salary
                    bulk_entries.append(PayrollItem(payroll=payroll_instance, employee=employee, item_type='basic_salary', amount=basic_salary,  entry='debit'))
                    # save salary grade
                    bulk_entries.append(PayrollItem(payroll=payroll_instance, employee=employee, item_type='salary_grade', dependency=salary_grade.id))
                    # save step
                    bulk_entries.append(PayrollItem(payroll=payroll_instance, employee=employee, item_type='step', dependency=salary_grade.grade_step.id))
                    # save tax
                    bulk_entries.append(PayrollItem(payroll=payroll_instance, employee=employee, item_type='tax', amount=income_tax, entry='credit'))
                    # save employer & employee ssnit
                    bulk_entries.append(PayrollItem(payroll=payroll_instance, employee=employee, item_type='employer_ssnit', amount=employer_ssnit, entry='credit'))
                    bulk_entries.append(PayrollItem(payroll=payroll_instance, employee=employee, item_type='employee_ssnit', amount=employee_ssnit, entry='credit'))
                    # save tax relief
                    bulk_entries.append(PayrollItem(payroll=payroll_instance, employee=employee, item_type='tax_relief', amount=tax_relief, entry='debit'))

                    # print(f"basic: {basic_salary} - tax: {income_tax} 'step: {step} - tax relief: {tax_relief} - ssnit employer: {employer_ssnit} - ssnit employee: {employee_ssnit} - net: {net}")

                    logger.info(f"Employee: {employee} Total Credit: {total_credit} - Total Debit: {total_debit}")

                    """Test double entry"""
                    logger.info("Double entry check, total credit against total debit")

                    if total_credit != total_debit:
                        msg = f"{employee}: Total credit {total_credit} differs from debit {total_debit}"
                        logger.warning(msg)
                        errors.append(msg)
                        error_entries.append(PayrollError(employee=employee, payroll=payroll_instance, error_category='double_entry'))
                        invalid_employees.add(employee.id)
                        # clear employee records from PayrollItem
                        continue                   

                    """Unlike my first version which was made in PHP (CodeIgniter) that strictly required that all data about employee must be intact before processing, this version should inform the admin of missing/vital details of certain employees and give them the option to proceed with processing without those employee(s). However, the system will document or keep these employees along with what they lacked whether (bank, salary grade, basic salary etc). Also, the system will be able to process the payroll without the mapping of real chart of account to payroll items such loans, credit unions, salary items etc, but in processing the processed payrolls for payment, those details will be mandatory since eventually, these funds must hit final accounts"""

                # for                
                # Filter out employee that has double entry issue..exclude them from payrollItem
                bulk_entries = [entry for entry in bulk_entries if entry.employee.id not in invalid_employees]

                # if error mode is strict, keep reporting when there are errors
                if error_mode == 'strict':
                    if errors:
                        # Strict mode: abort and return the list of errors for the template
                        logger.warning(f"Strict mode aborted due to {len(errors)} error(s).")
                        return JsonResponse({'status':'fail', 'message':list(errors), 'option':True}, safe=False)
                    else:
                        # Strict mode: processed without warnings
                        logger.info("Strict mode processing: No errors found.")
                        payroll_instance.save()
                        PayrollItem.objects.bulk_create(bulk_entries)
                        success_message = f"Payroll processed {len(synthetic_employees)} employee(s) successfully"         
                else:
                    # Mute mode: Process regardless of errors but saved for later reference
                    logger.info("Mute mode: Processing with errors logged for review.")
                    # if there are errors, save the error related object and save payroll and commit..
                    payroll_instance.save()
                    PayrollItem.objects.bulk_create(bulk_entries)
                    
                    if errors and error_entries:
                        # Error saved for future reference
                        logger.warning(f"Processed {len(synthetic_employees)} employee(s) with {len(error_entries)} warning(s). Errors logged.")
                        PayrollError.objects.bulk_create(error_entries)
                        success_message = f"Payroll processed {len(synthetic_employees)} employee(s) successfully with {len(error_entries)} warning(s)"
                    else:
                        # No warnings, mute mode was effectively a clean run
                        logger.info("Mute mode processed successfully without warnings.")
                        success_message = f"Payroll processed {len(synthetic_employees)} employee(s) successfully"
                # Final log and success response if everything is clean
                logger.info(success_message)
                return JsonResponse({'status': 'success', 'message': success_message})

            # try

        # with transaction
    
            except DatabaseError as e:
                logger.error(e)
                self.form_invalid(form)
                return JsonResponse({'status':'fail', 'message':'A database error occured while processing payroll. Please try again later'})
            except IntegrityError as e:
                logger.error(e)
                self.form_invalid(form)
                return JsonResponse({'status':'fail', 'message':"An error occured during processing. Please try again later"})

    def form_invalid(self, form):
        errors = form.errors
        return JsonResponse({'errors': errors}, status=400)

class PayrollListView(LoginRequiredMixin, ListView):
    model = Payroll
    template_name = 'hr/payroll/payroll_list.html'
    context_object_name = 'payroll_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Payroll Records'
        return context

class PayrollDetailView(LoginRequiredMixin, DetailView):
    model = Payroll
    template_name = 'hr/payroll/payroll_detail.html'
    context_object_name = 'payroll'

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        payroll = self.get_object()
        context['title'] = f"{payroll}"
        # Get distinct employees and for each employee, get net
        payroll_employees = []
        employees = Employee.objects.filter(payroll_items__payroll=self.get_object()).distinct().prefetch_related(
            Prefetch(
                'payroll_items',
                queryset=PayrollItem.objects.filter(payroll=payroll, item_type='bank'),
                to_attr='bank_items'
            ),
            Prefetch(
                'payroll_items',
                queryset=PayrollItem.objects.filter(payroll=payroll, item_type='salary_grade'),
                to_attr='salary_grade_items'
            )
        )

        for employee in employees:
            # Ensure bank item returned  valid data to avoid ValueError/AttributeError Exception
            bank_item = employee.bank_items[0] if employee.bank_items else None
            # Repeat same for salary_grade_item
            salary_grade_item = employee.salary_grade_items[0] if employee.salary_grade_items else None

            # Retrieve actual bsnk and salary grade data
            net_salary = bank_item.amount or 0
            salary_grade = salary_grade_item.description or 'N/A'
            bank_name = employee.bank.bank_name or 'N/A'
            branch = employee.branch or 'N/A'
            
            payroll_employees.append({
                'employee': f"{employee.first_name} {employee.last_name}",
                'net_salary': net_salary,
                'bank_name': f"{bank_name} ({branch})", 
                'account_number':employee.account_number or 'N/A'
            })
            context['payroll_employees'] = payroll_employees
        # for

        # Get distinct bank involved in this payroll and compute the total of employee's net salary under each bank

        payroll_banks = Bank.objects.filter(employees__payroll_items__payroll=payroll).distinct().annotate(
            total_amount=Sum('employees__payroll_items__amount', filter=Q(employees__payroll_items__payroll=payroll, employees__payroll_items__item_type='bank')), 
            employee_count=Count('employees', distinct=True, filter=Q(employees__payroll_items__payroll=payroll))
            )
        for bank in payroll_banks:
            pprint(vars(bank))


        context['payroll_banks'] = [
            {'bank_name':bank.bank_name, 'amount': bank.total_amount, 'employee_count':bank.employee_count}

            for bank in payroll_banks
        ]

        context['payroll_errors'] = PayrollError.objects.filter(payroll=payroll)


        return context

@login_required  
def delete_payroll(request, pk):
    payroll = Payroll.objects.get(id=pk)

    if request.method == "POST":
        payroll.delete()
        messages.success(request, f"{payroll} successfully deleted")
        return redirect('payroll-list')

    return render(request, 'core/delete.html', {'obj':payroll, 'title': f'Delete {payroll}?'})



class PayrollPayslipListView(LoginRequiredMixin, ListView):
    model = Payroll
    template_name = 'hr/payroll/payslip_list.html'
    context_object_name = 'payrolls'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Payslips'
        return context
    
    def get(self, request, *args, **kwargs):
        # Ensure the request header is an ajax request
        if request.headers.get('x-requested-with') == "XMLHttpRequest":
            payroll_id = request.GET.get('payroll_id')
            payroll = get_object_or_404(Payroll, id=payroll_id)

            # Get employees for this payroll and related items from payroll items
            payroll_employees = Employee.objects.filter(payroll_items__payroll=payroll).distinct().prefetch_related(
                Prefetch(
                    'payroll_items',
                    queryset=PayrollItem.objects.filter(payroll=payroll),
                    to_attr='all_payroll_items'
                )
            )
            employee_data = []
            for employee in payroll_employees:
                basic_salary = None; gross_salary = None; net_salary = None; 
                earning = None; deduction = None; tax = None; employee_ssnit = None

                for item in employee.all_payroll_items:
                    if not basic_salary and item.item_type == 'basic_salary':
                        basic_salary = item.amount
                    if not gross_salary and item.item_type == 'gross_salary':
                        gross_salary = item.amount
                    if not net_salary and item.item_type == 'net_salary':
                        net_salary = item.amount
                    if not earning and item.item_type == 'earning':
                        earning = item.amount
                    if not deduction and item.item_type == 'deduction':
                        deduction = item.amount
                    if not tax and item.item_type == 'tax':
                        tax = item.amount
                    if not employee_ssnit and item.item_type == 'employee_ssnit':
                        employee_ssnit = item.amount

                    # Exit if all match are found
                    if basic_salary and gross_salary and net_salary and tax and employee_ssnit and earning and deduction:
                        break
                
                employee_data.append({
                    'id':employee.id,
                    'employee_id':employee.employee_id,
                    'employee':f"{employee.first_name} {employee.last_name}",
                    'basic_salary': basic_salary,
                    'gross_salary':gross_salary,
                    'net_salary':net_salary,
                    'tax':tax,
                    'employee_ssnit':employee_ssnit,
                    'earning':earning,
                    'deduction':deduction
                })

            return JsonResponse({'employees':employee_data}, safe=False)
                   

        return super().get(request, *args, **kwargs)

def generate_payslip(request, uri_params):
    from django.http import Http404

    # extract employee_id and payroll_id from params
    try:
        employee_id, payroll_id = uri_params.split('_')
    except ValueError:
        raise Http404("Invalid URI Parameters")

    try:
        employee = Employee.objects.get(employee_id=employee_id)
        payroll = Payroll.objects.get(id=payroll_id) 
    except Employee.DoesNotExist:
        raise Http404("Employee Not Found")
    except Payroll.DoesNotExist:
        raise Http404("Payroll Not Found")
    

    # get payroll items and fetch earnings & deductions
    payroll_items = PayrollItem.objects.filter(payroll=payroll, employee=employee)
    earnings = []
    deductions = []
    basic_salary = None;  tax_relief = None

    tax = {}; ssnit = {}; loans = []; unions = []; other_deductions = []

    for item in payroll_items:
        item_type = item.item_type
        entry = item.entry
        amount = item.amount
        # retrieve all items with type 'salary item' 
        if item_type == 'salary_item' and entry == 'debit':
            earnings.append({'item':item.salary_item.alias_name, 'amount':amount })
        
        # for items of type tax, ssnit, loan etc with a credit entry, these are deductions
        elif item_type == 'tax':
            tax = {'item':'Income Tax', 'amount':amount }
        elif item_type == 'employee_ssnit':
             ssnit = {'item':'SSNIT (Employee)', 'amount':amount}
        elif item_type == 'loan':
             loans.append({'item': f"Loan ({ item.loan.get_loan_type_display() })", 'amount':amount})
        elif item_type == 'credit_union':
             unions.append({'item':f"{item.credit_union.union_name}", 'amount':amount})
        elif item_type == 'salary_item' and entry == 'credit':
             other_deductions.append({'item':item.salary_item.alias_name, 'amount':amount })
        elif item_type == 'basic_salary':
             basic_salary = amount
        elif item_type == 'tax_relief':
            tax_relief = amount
    # for
    
    # Ensure deduction_list are arranged in this order; tax, ssnit, loan, credit union an
    deductions.extend(filter(None, [tax, ssnit]))
    deductions.extend(loans)
    deductions.extend(unions)
    deductions.extend(other_deductions)


    # make the basic salary first item in the earning list
    if basic_salary is not None:
        earnings.insert(0, {'item':'Basic Salary', 'amount':basic_salary})
        
    # compute for annual salary 
    annual_salary = (basic_salary * 12) if basic_salary is not None else None

    gross_salary = sum(item['amount'] for item in earnings)
    total_deductions = sum(item['amount'] for item in deductions)
    net_salary = gross_salary - total_deductions


    context = {
        'title':f"Staff Payslip",
        'payroll':payroll,
        'employee':employee,
        'earnings':earnings,
        'deductions':deductions,
        'gross_salary':gross_salary,
        'net_salary':net_salary,
        'annual_salary':annual_salary,
        'tax_relief':tax_relief,
        'total_deductions':total_deductions
    }

    return render(request, 'core/document/payslip_printout.html', context)

# Bank 

class BankListView(LoginRequiredMixin, ListView):
    model = Bank 
    template_name = 'hr/payroll/bank_list.html'
    context_object_name = 'bank_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Banks"
        return context

class BankCreateView(LoginRequiredMixin, CreateView):
    model = Bank
    template_name = 'hr/payroll/bank_form.html'
    fields = ['bank_name']
    success_url = reverse_lazy('bank-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Add Bank"
        return context

    def form_valid(self, form):

        messages.success(self.request, f"New bank [{self.get_object()}] successfully created")
        return super().form_valid(form)

class BankUpdateView(LoginRequiredMixin, UpdateView):
    model = Bank
    template_name = 'hr/payroll/bank_form.html'
    fields = ['bank_name']
    success_url = reverse_lazy('bank-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Update {self.get_object()}"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"New bank [{self.get_object()}] successfully updated")
        return super().form_valid(form)
    
class BankEmployeeDetailView(LoginRequiredMixin, DetailView):
    model = Bank 
    template_name = 'hr/generic/item_detail.html'
    context_object_name = 'bank'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"{self.get_object()} Employees"
        context['item'] = 'bank'

        # fetch list of employees saving in this bank
        context['employees'] = Employee.objects.filter(bank=self.get_object())
        return context

def delete_bank(request, pk):
    bank = Bank.objects.get(id=pk)

    if request.method == "POST":
        bank.delete()
        messages.success(request, f"{bank} successfully deleted")
        return redirect(reverse_lazy('bank-list'))

    return render(request, 'core/delete.html', {'title': f"Delete {bank}?", 'obj':bank })

class PayrollVoucherDetailView(LoginRequiredMixin, DetailView):
    model = Payroll
    template_name = 'hr/payroll/payroll_voucher.html'
    context_object_name = 'payroll'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"{self.get_object()} - Initiate Payment Voucher"
        payroll= self.get_object()
        # print(payroll)
        # get distinct bank and use it 
        payroll_banks = Bank.objects.filter(employees__payroll_items__payroll=payroll).distinct()
        
        bank_totals = []  # Store results for each bank
        total_vouchers = 0
        reconcile_status = 0
        for bank in payroll_banks:
            # pprint(vars(bank))

            # Filter payroll items related to the current bank
            payroll_items = PayrollItem.objects.filter(
                payroll=payroll,
                employee__bank=bank  # Filter employees in this bank
            )
            print(bank.bank_name)

            # Filter out bank total 

            bank_balance = payroll_items.filter(item_type='bank', bank=bank).values('bank').aggregate(total=Sum('amount'))['total'] or 0

            # Get earning salary items total (grouping by salary_item foreign key)
            earning_salary_items = (
                payroll_items.filter(item_type='salary_item', entry='debit')
                .values('salary_item__id', 'salary_item__alias_name')  # Group by salary_item ForeignKey
                .annotate(total=Sum('amount'))
            )
            total_earning_salary_items = sum(si['total'] for si in earning_salary_items)

            deduction_salary_items = (
                payroll_items.filter(item_type='salary_item', entry='credit')
                .values('salary_item__id', 'salary_item__alias_name')  # Group by salary_item ForeignKey
                .annotate(total=Sum('amount'))
            )
            total_deduction_salary_items = sum(si['total'] for si in deduction_salary_items)

            # Get credit unions total (grouping by credit_union foreign key)
            credit_unions = (
                payroll_items.filter(item_type='credit_union')
                .values('credit_union__id', 'credit_union__union_name')  # Group by credit_union ForeignKey
                .annotate(total=Sum('amount'))
            )
            total_credit_unions = sum(cu['total'] for cu in credit_unions)

            # Get loans total (grouping by loan type)
            loans_grouped_by_type = (
                payroll_items.filter(item_type='loan')
                .values('loan__id', 'loan__loan_type')  # Group by loan type
                .annotate(total=Sum('amount'))
            )          
            total_loans = sum(l['total'] for l in loans_grouped_by_type)
            loans = [
                {
                    'loan_type': Loan.objects.get(id=item['loan__id'], loan_type=item['loan__loan_type']).get_loan_type_display(),
                    'total': item['total']
                }
                for item in loans_grouped_by_type
            ]


            # print(loans)
       
            # Totals for deductions like SSNIT, Tax
            total_employee_ssnit = payroll_items.filter(item_type='employee_ssnit').aggregate(total=Sum('amount'))['total'] or 0
            total_employer_ssnit = payroll_items.filter(item_type='employer_ssnit').aggregate(total=Sum('amount'))['total'] or 0
            total_tax = payroll_items.filter(item_type='tax').aggregate(total=Sum('amount'))['total'] or 0
            
            total_tax_relief = payroll_items.filter(item_type='tax_relief').aggregate(total=Sum('amount'))['total'] or 0

            # Totals for basic salary
            total_basic_salaries = payroll_items.filter(item_type='basic_salary').aggregate(total=Sum('amount'))['total'] or 0
            
            total_debit = total_earning_salary_items + total_basic_salaries + total_tax_relief + total_employer_ssnit
            total_credit = bank_balance + total_deduction_salary_items + total_credit_unions + total_loans + total_employee_ssnit + total_tax + total_employer_ssnit

            # print(total_salary_items)

            # for si in salary_items:
            #     pprint(si)

            pprint(f"{total_debit} - {total_credit}")
            if Decimal(total_debit) == Decimal(total_credit):
                reconcile_status += 1

            # pprint(payroll_items)

            bank_totals.append({
                'bank_name':bank.bank_name,
                'bank_balance':bank_balance,
                'earning_salary_items': list(earning_salary_items),
                'deduction_salary_items': list(deduction_salary_items),
                'credit_unions': list(credit_unions),
                'loans': list(loans),
                'total_employee_ssnit': total_employee_ssnit,
                'total_employer_ssnit': total_employer_ssnit,
                'total_earning_salary_items': total_earning_salary_items,
                'total_deduction_salary_items': total_deduction_salary_items,
                'total_loans': total_loans,
                'total_credit_unions': total_credit_unions,
                'total_basic_salaries': total_basic_salaries,
                'total_tax':total_tax,
                'total_tax_relief':total_tax_relief,
                'total_debit':total_debit,
                'total_credit':total_credit

            })
            total_vouchers += 1

        # pprint(bank_totals)
        context['transactions'] = bank_totals
        context['total_vouchers'] = total_vouchers
        context['reconcile_status'] = reconcile_status
        print(f"{total_vouchers} {reconcile_status}")
        return context


    