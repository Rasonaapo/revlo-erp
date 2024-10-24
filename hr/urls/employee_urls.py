from django.urls import path
from hr.views.employee_views import  *
from hr.views.employee_json import *
from hr.views.leave_views import *

## Department
urlpatterns = [
    # path('', employee_views.index, name='home'),
    path('departments/', DepartmentListView.as_view(), name="department-list"),
    path('departments/add/', DepartmentCreateView.as_view(), name="department-add"),
    path('departments/<int:pk>/update/', DepartmentUpdateView.as_view(), name="department-update"),
    path('departments/<int:pk>/delete/', delete_department, name="department-delete"),
    path('departments/api/', DepartmentListApiView.as_view(), name="department-list-api"),
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
    path('employees/api/', EmployeeListApiView.as_view(), name='employee-list-api'),  # API for DataTables
    path('employees/<int:pk>/detail/', EmployeeDetailView.as_view(), name='employee-detail'),
    path('employees/add/', EmployeeCreateView.as_view(), name='employee-add'),
    path('employees/<int:pk>/update/', EmployeeUpdateView.as_view(), name="employee-update"),
    path('employees/<int:pk>/delete/', delete_employee, name="employee-delete"),
    path('employees/<int:pk>/photo-upload/', EmployeePhotoUpdateView.as_view(), name='employee-photo-upload'),
    path('employees/<int:pk>/documents/', EmployeeDocumentView.as_view(), name='employee-file-upload'),

]   

## Leave
urlpatterns +=[
        # Type
        path('leave-types/', LeaveTypeListView.as_view(), name='leave-type-list'),
        path('leave-types/api/', LeaveTypeAPIView.as_view(), name='leave-type-list-api'),
        path('leave-types/add/', LeaveTypeCreateView.as_view(), name='leave-type-add'),
        path('leave-types/<int:pk>/update/', LeaveTypeUpdateView.as_view(), name='leave-type-update'),
        path('leave-types/<int:pk>/delete/', delete_leave_type, name='leave-type-delete'),

        # Balance
        path('leave-balances/', LeaveBalanceListView.as_view(), name='leave-balance-list'),
        path('leave-balances/api/', LeaveBalanceAPIView.as_view(), name='leave-balance-list-api'),
        path('leave-balances/<int:pk>/update/', LeaveBalanceUpdateView.as_view(), name='leave-balance-update'),
        path('leave-requests/', LeaveRequestListView.as_view(), name='leave-request-list'),
        path('leave-requests/api/', LeaveRequestAPIView.as_view(), name='leave-request-list-api'),
        path('leave-requests/<int:pk>/add/', LeaveRequestCreateView.as_view(), name='leave-request-add'),
        path('leave-requests/<int:pk>/update/', LeaveRequestUpdateView.as_view(), name='leave-request-update'),
        path('public-holidays/', PublicHolidayListView.as_view(), name='holiday-list'),
        path('public-holidays/add/', PublicHolidayCreateView.as_view(), name='holiday-add'),
        path('public-holidays/<int:pk>/update/', PublicHolidayUpdateView.as_view(), name='holiday-update'),
        path('public-holidays/<int:pk>/delete/', delete_holiday, name='holiday-delete'),

]
