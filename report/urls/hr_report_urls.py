from django.urls import path

from ..views.hr_report_views import *

urlpatterns = [
     path('employees/', EmployeeListView.as_view(), name='employee-report')
]
