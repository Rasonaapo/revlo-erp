from django.urls import path
from hr.views.payroll_views import  *
from hr.views.payroll_json import *

# Salary Grade
urlpatterns = [
    path('salary-grades/', SalaryGradeListView.as_view(), name='salarygrade-list'),
    path('salary-grades/add/', SalaryGradeCreateView.as_view(), name='salarygrade-add'),
    path('salary-grades/<int:pk>/update/', SalaryGradeUpdateView.as_view(), name='salarygrade-update'),
    path('salary-grades/<int:pk>/delete/', delete_salary_grade, name='salarygrade-delete'),
    path('salary-grades/api/', SalaryGradeListApiView.as_view(), name="salarygrade-list-api"),

]