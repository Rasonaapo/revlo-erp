from typing import Any
from django import forms
from ..models.employee import JobHistory, Employee, Guarantor, Document, DocumentType, LeaveRequest
from datetime import date
from django.core.exceptions import ValidationError
import re
from django.utils.translation import gettext_lazy as _
from django.forms import modelformset_factory

class JobHistoryForm(forms.ModelForm):
    class Meta:
        model = JobHistory
        fields = ['employee', 'start_date', 'end_date', 'job']
        widgets = {
            'start_date': forms.DateInput(attrs={'type':'date', 'class':'datepicker'}),
            'end_date': forms.DateInput(attrs={'type':'date', 'class':'datepicker'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and start_date > date.today():
            raise ValidationError('start date cannot be in the future')
        
        if end_date and start_date and end_date <= start_date:
            raise ValidationError('End date must be after the start date')
        return cleaned_data
    
class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        exclude = ['created_at', 'updated_at']
        widgets = {
            'dob':forms.DateInput(attrs={'type':'date', 'class':'datepicker', 'required':'required'}),
        }

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
    
        cleaned_number = ''.join(filter(str.isdigit, phone_number))
        # number must be 10 digit and must begin with 0 or zero followed by any two prefix then 7 numbers
        if re.match(r'^0(23|24|25|53|54|55|59|27|57|26|56|28|20|50)\d{7}$', cleaned_number):
                return cleaned_number  # Valid Ghanaian phone number
        
        raise ValidationError(_("Invalid phone number, please use a valid Ghanaian phone number"))

    def clean_dob(self):
        dob = self.cleaned_data.get('dob')

        # dob must be older than 17 years..
        today = date.today()
        age = today.year - dob.year
        if today.month < dob.month or (today.month == dob.month and today.day < dob.day):
            age -= 1

        if age < 18:
            raise ValidationError(_("Age must be at least 18 years old"))
        
        return dob


    def __init__(self, *args, **kwargs):
        super(EmployeeForm, self).__init__(*args, **kwargs)
        self.fields['tin'].required = False

class GuarantorForm(forms.ModelForm):
    class Meta:
        model = Guarantor
        fields = ['guarantor_name', 'guarantor_phone_number']
        widgets = {
            'guarantor_phone_number': forms.TextInput(attrs={'class':'form-control'}),
            'gurantor_name': forms.TextInput(attrs={'class':'form-control'})
        }
    
    def clean_guarantor_phone_number(self):
        phone_number = self.cleaned_data.get('guarantor_phone_number')
    
        cleaned_number = ''.join(filter(str.isdigit, phone_number))
        # number must be 10 digit and must begin with 0 or zero followed by any two prefix then 7 numbers
        if re.match(r'^0(23|24|25|53|54|55|59|27|57|26|56|28|20|50)\d{7}$', cleaned_number):
                return cleaned_number  # Valid Ghanaian phone number
        
        raise ValidationError(_("Invalid guarantor phone number, please use a valid Ghanaian phone number"))

class DocumentUploadForm(forms.ModelForm):
    document_type = forms.ModelChoiceField(
        queryset=DocumentType.objects.all(),
        label='Document Type',
        widget = forms.Select(attrs={'class':'form-control'}),
        help_text="Select the document type"
    )
    document_file = forms.FileField(
        label='Document File',
        widget = forms.ClearableFileInput(attrs={'class':'form-control'})
    )
    class Meta:
        model = Document
        fields = ['document_type', 'document_file']
        exclude = ['employee']


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['start_date', 'days_requested', 'status']
        widgets = {
            'start_date': forms.DateInput(attrs={'type':'date', 'class':'datepicker'})
        }
    def __init__(self, *args, **kwargs):
        # Capture remaining_days from view context
        self.remaining_days = kwargs.pop('remaining_days', None)
        super(LeaveRequestForm, self).__init__(*args, **kwargs)

        if self.instance.pk:
            self.fields['status'].choices = [
                ('Pending', 'Pending'),
                ('Approved', 'Approved'),
                ('Rejected', 'Rejected'),
            ]
        else:
            self.fields['status'].choices = [
                ('Pending', 'Pending'),
                ('Approved', 'Approved')
            ]

    def clean_days_requested(self):
        days_requested = self.cleaned_data.get('days_requested')
        if days_requested > self.remaining_days:
            raise forms.ValidationError(f"Requested days cannot exceed {self.remaining_days} remaining days.")
        return days_requested

    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')
        if start_date < date.today():
            raise forms.ValidationError("Start date cannot be in the past.")
        return start_date
