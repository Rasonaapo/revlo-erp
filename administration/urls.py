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