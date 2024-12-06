from django.contrib import admin

# Register your models here.
from .models import Meeting, Attendance 

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('meeting', 'employee', 'check_in_time', )


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ('subject', 'meeting_date', 'sms_date', 'location', 'status', 'agenda', )
