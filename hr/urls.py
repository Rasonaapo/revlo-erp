from django.urls import path, include

urlpatterns = [
     path('employees/', include('hr.urls.employee_urls')),
     path('payroll/', include('hr.urls.payroll_urls')),
]
