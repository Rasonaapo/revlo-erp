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

# Loan
urlpatterns += [
    path('loans/', LoanListView.as_view(), name='loan-list'),
    path('loans/add/', LoanCreateView.as_view(), name='loan-add'),
    path('loans/<int:pk>/update/', LoanUpdateView.as_view(), name='loan-update'),
    path('loans/<int:pk>/delete/', LoanDeleteView.as_view(), name='loan-delete'),
    path('loans/api/', LoanListApiView.as_view(), name='loan-list-api'),
    path('loans/<int:pk>/detail/', LoanDetailView.as_view(), name='loan-detail'),
]

# Credit Union 
urlpatterns += [
      path('credit-unions/', CreditUnionListView.as_view(), name='creditunion-list'),
      path('credit-unions/<int:pk>/update/', CreditUnionUpdateView.as_view(), name='creditunion-update'),
      path('credit-unions/add/', CreditUnionCreateView.as_view(), name='creditunion-add'),
      path('credit-unions/<int:pk>/delete/', delete_credit_union, name='creditunion-delete'),
      path('credit-unions/<int:pk>/detail/', CreditUnionDetailView.as_view(), name='creditunion-detail'),
      path('credit-unions/api/', CreditUnionListApiView.as_view(), name='creditunion-list-api'),
      path('credit-unions/<int:pk>/set-employee-detail/', CreditUnionSetEmployeeDetailView.as_view(), name='creditunion-set-details'),
  
]