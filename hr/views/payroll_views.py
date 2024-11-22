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
from ..forms.payroll_forms import SalaryItemForm, LoanForm, CreditUnionForm

from hr.models.payroll import SalaryGrade
from .utils import compute_factor, get_filtered_staff_credit_union

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

            print(f"Employee to add: {employee_to_add}")
            print(f"Employee to remove: {employee_to_remove}")
            
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


