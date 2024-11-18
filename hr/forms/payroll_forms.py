from django.core.exceptions import ValidationError
from django import forms
from ..models.payroll import SalaryItem
from ..models.employee import Employee

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
        
