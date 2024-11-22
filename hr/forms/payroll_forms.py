from django.core.exceptions import ValidationError
from django import forms
from ..models.payroll import SalaryItem, Loan, CreditUnion
from ..models.employee import Employee
from datetime import date

class SalaryItemForm(forms.ModelForm):
    class Meta:
        model = SalaryItem
        exclude = ['created_at', 'updated_at', 'staff_source', 'eligible_employee_count']
        widgets = {
            'expires_on': forms.DateInput(
                attrs={'type':'date', 'class':'form-control'}
            ),
            'rate_dependency':forms.TextInput(
                attrs={'placeholder':'Eg. Number of Hours'}
            )

        }
    
    def __init__(self, *args, **kwargs):
        super(SalaryItemForm, self).__init__(*args, **kwargs)

        active_employees = Employee.objects.active()
        # We query for only active employees 
        self.fields['applicable_to'].queryset = active_employees
        self.fields['excluded_from'].queryset = active_employees

        self.fields['expires_on'].required = False
        self.fields['rate_dependency'].required = False

    def clean(self):
        cleaned_data = super().clean()
        applicable_to = cleaned_data.get('applicable_to')
        excluded_from = cleaned_data.get('excluded_from')
        step = cleaned_data.get('step')
        salary_grade = cleaned_data.get('salary_grade')
        job = cleaned_data.get('job')
        department = cleaned_data.get('department')
        designation = cleaned_data.get('designation')
        condition = cleaned_data.get('condition')

        # Check if `applicable_to` is used exclusively
        if applicable_to:
            # Ensure no other filter fields are in use if `applicable_to` is populated
            if any([step, salary_grade, job, department, designation]):
                raise ValidationError("If `applicable_to` is used, all other filters (step, salary grade, job, department, designation) must be empty.")

            # Ensure `excluded_from` is empty if `applicable_to` is used
            if excluded_from:
                raise ValidationError("If `applicable_to` is used, `excluded_from` must be empty.")

        # If `applicable_to` is not used, other filters can be used, and `excluded_from` is allowed
        elif not any([step, salary_grade, job, department, designation, condition]):
            raise ValidationError("If `applicable_to` is not used, at least one other filter (step, salary grade, job, department, designation, condition) must be specified.")

        return cleaned_data
        
class LoanForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ['employee', 'loan_type', 'status', 'principal_amount', 'interest_rate', 'duration_in_months', 'purpose', 'applied_on']

        widgets = {
            'applied_on':forms.DateInput(attrs={'type':'date' }),
            'purpose':forms.Textarea(attrs={'cols':4})
        }

    def __init__(self, *args, **kwargs):
        super(LoanForm, self).__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.active()
    
        if self.instance.pk:
            # self.fields.append('status')
            self.fields['status'].choices =  (('pending', 'Pending Approval'),
                                                ('approved', 'Approved'),
                                                ('rejected', 'Rejected'))
        else:
            self.fields['status'].choices =  (('pending', 'Pending Approval'),)

    def clean_applied_on(self):
        applied_on = self.cleaned_data.get('applied_on')

        # Ensure that applied on must not be in the past, at most today
        if applied_on > date.today():
            raise forms.ValidationError("Applied on must not be a future date")
        
        return applied_on

class CreditUnionForm(forms.ModelForm):
    class Meta:
        model = CreditUnion
        exclude = ['created_at', 'updated_at']


    def __init__(self, *args, **kwargs):
        super(CreditUnionForm, self).__init__(*args, **kwargs)

        # Ensure both applicable_to and exculded_from populates active employees
        active_employees = Employee.objects.active()
        self.fields['applicable_to'].queryset = active_employees
        self.fields['excluded_from'].queryset = active_employees
    
    def clean(self):
        cleaned_data =  super().clean()

        all_employee = cleaned_data.get('all_employee')
        applicable_to = cleaned_data.get('applicable_to')
        excluded_from = cleaned_data.get('excluded_from')
        department = cleaned_data.get('department')
        deduction_start_date = cleaned_data.get('deduction_start_date')
        deduction_end_date = cleaned_data.get('deduction_end_date')

        # Ensure that start date and end date aren't the same if only they're supplied

        # Check if all employee is checked
        if all_employee:
            # Ensure no other filter is used saved excluded from
            if any([applicable_to, department]):
                raise ValidationError("If 'all employee' is checked, you can not use either (applicable to and or department)")

        # Ensure excluded from goes with at least a filter
        if excluded_from and not any([all_employee, department, applicable_to]):
            raise ValidationError("If excluded from is selected, you must select at least one of (all staff, department or applicable to)")
        
        # if applicable to is used, ensure no other filter is selected
        if applicable_to and any([all_employee, department]):
                raise ValidationError("If `applicable_to` is used, all other filters (department, all staff) must be empty.")
        
        return cleaned_data


    