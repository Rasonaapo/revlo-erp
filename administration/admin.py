from django.contrib import admin

# Register your models here.
from .models import Meeting, Attendance, DocumentCategory, Vendor, BusinessDocument, BusinessDocumentFile, DocumentCategory

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('meeting', 'employee', 'check_in_time', )


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ('subject', 'meeting_date', 'sms_date', 'location', 'status', 'agenda', )

@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', )

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone_number', 'address', )

@admin.register(BusinessDocument)
class BusinessDocumentAdmin(admin.ModelAdmin):
    list_display = ('document_name', 'associated_entity', 'vendor', 'expiration_date', 'notes', )

@admin.register(BusinessDocumentFile)
class BusinessDocumentFileAdmin(admin.ModelAdmin):
    list_display = ('business_document', 'document_category', 'document_file', )
