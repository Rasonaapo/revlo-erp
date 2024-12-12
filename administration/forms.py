
from django import forms
from datetime import date
from . models import Meeting, Vendor, BusinessDocument, BusinessDocumentFile, DocumentCategory
from django.core.exceptions import ValidationError
import re
from django.utils.translation import gettext_lazy as _

class MeetingForm(forms.ModelForm):
    class Meta:
        model = Meeting
        exclude = ['created_at', 'updated_at']
        widgets = {
            'meeting_date':forms.DateTimeInput(attrs={'type':'datetime', 'class':'datetimepicker'}),
            'sms_date':forms.DateTimeInput(attrs={'type':'datetime', 'class':'datetimepicker'})
        } 
    
    def __init__(self, *args, **kwargs):
        super(MeetingForm, self).__init__(*args, **kwargs)
        self.fields['sms'].required = True
        self.fields['job'].required = False
        self.fields['department'].required = False
        self.fields['salary_grade'].required = False

    def clean(self):
        cleaned_data = super().clean()

        meeting_date = cleaned_data.get('meeting_date')
        sms_date = cleaned_data.get('sms_date')

        # Ensure SMS date & time is less or precedes meeting date & time
        if sms_date and meeting_date and  sms_date >= meeting_date:
            raise forms.ValidationError("SMS date & time must precede the actual day of the meeting")
        return cleaned_data
    
    def clean_meeting_date(self):
        meeting_date = self.cleaned_data.get('meeting_date')
        if meeting_date.date() < date.today():
            raise forms.ValidationError("Meeting date must not be in the past")
        return meeting_date
    
    def clean_sms_date(self):
        sms_date = self.cleaned_data.get('sms_date')
        if sms_date.date() < date.today():
            raise forms.ValidationError("SMS date must not be in the past")
        return sms_date

class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor 
        exclude = ['created_at', 'updated_at']
        widgets = {
            'address':forms.Textarea(attrs={'class':'form-control', 'rows':'4'}),
            'notes':forms.Textarea(attrs={'class': 'quill-editor', 'rows':'4'})
        }


    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
    
        cleaned_number = ''.join(filter(str.isdigit, phone_number))
        # number must be 10 digit and must begin with 0 or zero followed by any two prefix then 7 numbers
        if re.match(r'^0(23|24|25|53|54|55|59|27|57|26|56|28|20|50)\d{7}$', cleaned_number):
                return cleaned_number  # Valid Ghanaian phone number
        
        raise ValidationError(_("Invalid phone number, please use a valid Ghanaian phone number"))

class BusinessDocumentForm(forms.ModelForm):
    class Meta:
        model = BusinessDocument
        fields = ['document_name', 'vendor', 'expiration_date', 'associated_entity', 'notes']
        widgets = {
            'expiration_date':forms.DateInput(attrs={'class':'datepicker', 'readonly':True}),
            'notes':forms.Textarea(attrs={'class':'quil-editor', 'rows':'4'}),
            # 'vendor':forms.Select(attrs={''})
        }

    def __init__(self, *args, **kwargs):
        super(BusinessDocumentForm, self).__init__(*args, **kwargs)

        self.fields['document_name'].help_text = "Please note that file(s) will be uploaded after form submission"
            
class BusinessDocumentUploadForm(forms.ModelForm):

    # document_category = forms.ModelChoiceField(
    #     queryset=DocumentCategory.objects.all(),
    #     widget={forms.Select(attrs={'class':'form-control'})},
    #     label='Document Category',
    
    # )
    # document_file = forms.FileField(
    #     label='File Upload',
    #     widget={forms.ClearableFileInput(attrs={'class':'form-control'})},
    #     help_text="Note: File(s) uploaded will be partially renamed",
    # )

    class Meta:
        model = BusinessDocumentFile
        fields = ['document_category', 'document_file']

        exclude = ['business_document']
        widgets = {
            'document_category':forms.Select(attrs={'class':'form-control select2'}),
            'document_file':forms.ClearableFileInput(attrs={'class':'form-control'})
        }
    
    def __init__(self, *args, **kwargs):
        super(BusinessDocumentUploadForm, self).__init__(*args, **kwargs)

