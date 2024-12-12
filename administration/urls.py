from django.urls import path
from .views import *

## Meeting 
urlpatterns = [
    path('meetings/', MeetingListView.as_view(), name='meeting-list'),
    path('meetings/api/', MeetingAPIView.as_view(), name='meeting-list-api'),
    path('meetings/<int:pk>/update/', MeetingUpdateView.as_view(), name='meeting-update'),
    path('meetings/add/', MeetingCreateView.as_view(), name='meeting-add'),
    path('meetings/<int:pk>/delete/', delete_meeting, name='meeting-delete'),     
    path('meetings/<int:pk>/detail/', MeetingDetailView.as_view(), name='meeting-detail'),
    path('meetings/<int:pk>/update-attendance/', update_attendance, name='attendance-update'),
]

## Vendor
urlpatterns += [
     path('vendors/', VendorListView.as_view(), name='vendor-list'),
     path('vendors/api/', VendorAPIView.as_view(), name='vendor-list-api'),
     path('vendors/add/', VendorCreateView.as_view(), name='vendor-add'),
     path('vendors/<int:pk>/update/', VendorUpdateView.as_view(), name='vendor-update'),
     path('vendors/<int:pk>/detail/', VendorDetailView.as_view(), name='vendor-detail'),
     path('vendors/<int:pk>/delete/', delete_vendor, name='vendor-delete'),
]
## Business Docs
urlpatterns += [
    path('business-documents/', DocumentListView.as_view(), name='document-list'),
    path('business-documents/api/', DocumentAPIView.as_view(), name='document-list-api'),
    path('business-documents/add/', DocumentCreateView.as_view(), name='document-add'),
    path('business-documents/<int:pk>/files/', DocumentUploadDetailView.as_view(), name='document-upload'),
    path('business-documents/<int:pk>/update/', DocumentUpdateView.as_view(), name='document-update'),
    path('business-documents/<int:pk>/delete/', delete_document, name='document-delete'),
    path('business-documents/<int:pk>/detail/', DocumentDetailView.as_view(), name='document-detail'),
    path('business-documents/files/<int:pk>/delete/', delete_document_file, name="document-file-delete"),
]