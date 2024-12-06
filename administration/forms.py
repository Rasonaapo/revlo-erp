
from django import forms
from datetime import date
from . models import Meeting 

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

