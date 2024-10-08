from django.urls import path
from hr.views.employee_views import  *

urlpatterns = [
    # path('', employee_views.index, name='home'),
    path('departments/', DepartmentListView.as_view(), name="department-list"),
    path('departments/add/', DepartmentCreateView.as_view(), name="department-add"),
    path('departments/<int:pk>/update/', DepartmentUpdateView.as_view(), name="department-update"),
    path('departments/<int:pk>/delete/', delete_department, name="department-delete"),

]

## Job
urlpatterns += [
    path('jobs/', JobListView.as_view(), name='job-list'),
    path('jobs/add/', JobCreateView.as_view(), name='job-add'),
    path('jobs/<int:pk>/update/', JobUpdateView.as_view(), name="job-update"),
    path('jobs/<int:pk>/delete/', delete_job, name="job-delete"),
]

## Job Histories
urlpatterns += [
    path('job-histories/', JobHistoryListView.as_view(), name='job-history-list'),
    path('job-histories/add/', JobHistoryCreateView.as_view(), name='job-history-add'),
    path('job-histories/<int:pk>/update/', JobHistoryUpdateView.as_view(), name="job-history-update"),
    path('job-histories/<int:pk>/delete/', delete_job_history, name="job-history-delete"),
]

## Employee
urlpatterns += [
    path('employees/', EmployeeListView.as_view(), name='employee-list'),
    path('employees/add/', EmployeeCreateView.as_view(), name='employee-add'),
    path('employees/<int:pk>/update/', EmployeeUpdateView.as_view(), name="employee-update"),
    path('employees/<int:pk>/delete/', delete_employee, name="employee-delete"),
    path('employees/<int:pk>/photo-upload/', EmployeePhotoUpdateView.as_view(), name='employee-photo-upload'),
]
