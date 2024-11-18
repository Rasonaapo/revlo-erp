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
    path('salary-grades/<int:pk>/employees/', SalaryGradeEmployeeDetailView.as_view(), name="salarygrade-employee"),

]

# Tax
urlpatterns += [
    path('setup-tax/', setup_tax, name='setup-tax'),
    path('load-tax/', load_tax, name='load-tax'),
    path('test-tax/<str:amount>/', test_tax, name='test-tax'),

]

# Salary Item
urlpatterns += [
    path('salary-items/', SalaryItemListView.as_view(), name='salaryitem-list'),
    path('salary-items/add/', SalaryItemCreateView.as_view(), name="salaryitem-add"),
    path('salary-items/api/', SalaryItemListApiView.as_view(), name="salaryitem-list-api"),
    path('salary-items/<int:pk>/update/', SalaryItemUpdateView.as_view(), name='salaryitem-update'),
    path('load-salary-items/', load_salary_items, name='load-salary-items'),
    path('salary-items/<int:pk>/delete/', delete_salary_item, name='salaryitem-delete'),
    path('salary-items/<int:pk>/employees/', SalaryItemEmployeeDetailView.as_view(), name='salaryitem-employee'),
    path('salary-items/<int:pk>/set-variable/', SalaryItemVariableDetailView.as_view(), name="salaryitem-variable"),
]