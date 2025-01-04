from django.urls import path
from ..views.payroll_report_views import *


# Payroll Reports
urlpatterns = [
     path('employee-ssnit/', EmployeeSSNITDetailView.as_view(), name='employee-ssnit-report')
]
