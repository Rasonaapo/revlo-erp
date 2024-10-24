from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse
from hr.models.employee import Employee, Department
from django_datatables_view.base_datatable_view import BaseDatatableView
from django.utils.html import escape
from datetime import date
from django.db.models import Q, Count
import json
from django.urls import reverse
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from hr.models.employee import *
from django.urls import reverse_lazy
from django import forms
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from datetime import timedelta
from ..forms.employee_forms import LeaveRequestForm
from .utils import calculate_end_date, get_current_year
import pdb
from django.db import transaction

class LeaveTypeListView(LoginRequiredMixin, ListView):
    model = LeaveType
    template_name = 'hr/leave/leave_type_list.html'
    context_object_name = 'leave_type_list'

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        context['title'] = 'Leave Types'
        return context
    
class LeaveTypeAPIView(LoginRequiredMixin, BaseDatatableView):
    model = LeaveType
    columns = ['id', 'name', 'entitlement', 'method', 'allow_rollover', 'created_at']

    def render_column(self, row, column):
        if column == 'created_at':
            return row.created_at.strftime('%d %b, %Y')  # Format the created_at field
        if column == 'allow_rollover':
            return row.allow_rollover
        if column == 'id':
            return row.id
        
        return super().render_column(row, column)
      
    def get_initial_queryset(self):
        return LeaveType.objects.all()

    def filter_queryset(self, qs):
        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(entitlement__icontains=search) |
                Q(method__icontains=search) 
            )
        return qs
    
class LeaveTypeCreateView(LoginRequiredMixin, CreateView):
    model = LeaveType
    template_name = 'hr/leave/leave_type_form.html'
    fields = ['name', 'entitlement', 'method', 'allow_rollover']
    success_url = reverse_lazy('leave-type-list')

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        context['title'] = 'Add Leave Type'
        return context
    
    def form_valid(self, form):
        leave_type = form.save()
        # update all employees with this new leave type
        employees = Employee.objects.all()
        with transaction.atomic():
            valid_status = ['active', 'probation', 'inactive', 'on_leave']
            for employee in employees:
                if employee.status in valid_status:
                    LeaveBalance.objects.create(
                    employee=employee,
                    leave_type=leave_type,
                    accrued_days=leave_type.entitlement,
                    used_days=0.0
                )
            messages.success(self.request, f"{form.instance.name} leave type created successfully")
            return super().form_valid(form)

class LeaveTypeUpdateView(LoginRequiredMixin, UpdateView):
    model = LeaveType
    template_name = 'hr/leave/leave_type_form.html'
    fields = ['name', 'entitlement', 'method', 'allow_rollover']
    context_object_name = 'leave_type'
    success_url = reverse_lazy('leave-type-list')

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        context['title'] = f'Modify {self.get_object().name} Type'
        return context

    def form_valid(self, form):
        messages.success(self.request, f"{self.get_object().name} leave type updated successfully")
        return super().form_valid(form)

def delete_leave_type(request, pk):
    leave_type = LeaveType.objects.get(id=pk)

    if request.method == "POST":
        leave_type.delete()
        messages.success(request, f"{leave_type} was deleted successfully")
        return redirect('leave-type-list')

    return render(request, 'core/delete.html', {'obj':leave_type, 'title': f'Delete {leave_type}?'})
 
class LeaveBalanceListView(LoginRequiredMixin, ListView):
    model = LeaveBalance
    template_name = 'hr/leave/leave_balance_list.html'
    context_object_name = 'leave_balance_list'

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        context['title'] = 'Leave Balances'
        context['employee_list'] = Employee.objects.all()
        context['leave_type_list'] = LeaveType.objects.all()
        return context
    
class LeaveBalanceAPIView(LoginRequiredMixin, BaseDatatableView):
    model = LeaveBalance
    columns = ['id', 'employee', 'leave_type', 'accrued_days', 'used_days', 'remaining_days', 'created_at', 'updated_at']

    def render_column(self, row, column):
        if column == 'created_at':
                return row.updated_at.strftime('%d %b, %Y') if row.updated_at else '-'  # Format the created_at field      
        if column == 'remaining_days':
            return row.remaining_days()
        
        if column == 'id':
            return row.id
        
        if column == 'employee':
            employee = row.employee
            return {'name':f"{employee.first_name} {employee.last_name}", 'photo':employee.photo.url, 'status':employee.status}
             
        return super().render_column(row, column)
      
    def get_initial_queryset(self):
        return LeaveBalance.objects.all()

    def filter_queryset(self, qs):
        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(employee__first_name__icontains=search) |
                Q(employee__last_name__icontains=search) |
                Q(leave_type__name__icontains=search) 
            )
                # Additional filters for employee and leave type
        employee_id = self.request.GET.get('employee', None)
        leave_type_id = self.request.GET.get('leave_type', None)

        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        
        if leave_type_id:
            qs = qs.filter(leave_type_id=leave_type_id)
        return qs

class LeaveBalanceUpdateView(LoginRequiredMixin, UpdateView):
    model = LeaveBalance
    template_name = 'hr/leave/leave_balance_form.html'
    fields = ['accrued_days']
    context_object_name = 'leave_balance'
    success_url = reverse_lazy('leave-balance-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Update {self.get_object().employee} Leave Balance"

        return context

    def form_valid(self, form):
        accrued_days = form.cleaned_data['accrued_days']
        entitlement = self.get_object().leave_type.entitlement
        # Ensure that accrued days does not exceed original entitlement
        if accrued_days > entitlement:
            form.add_error('accrued_days', f"Accrued days cannot exceed original entitlement of {entitlement} days")
            return self.form_invalid(form)

        messages.success(self.request, f"{self.get_object().employee} leave balance successfully updated")
        return super().form_valid(form)
    
    ## Request 
class LeaveRequestListView(LoginRequiredMixin, ListView):
        template_name = 'hr/leave/leave_request_list.html'
        model = LeaveRequest
        context_object_name = 'leave_request_list'

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['title'] = 'Leave Requests'
            context['leave_type_list'] = LeaveType.objects.all()
            context['employee_list'] = Employee.objects.all()

            return context

class LeaveRequestAPIView(LoginRequiredMixin, BaseDatatableView):
    model = LeaveRequest
    columns = ['id', 'employee', 'leave_type', 'days_requested', 'updated_at', 'start_date', 'end_date', 'created_at', 'status']

    def render_column(self, row, column):
        if column == 'created_at':
                return row.updated_at.strftime('%d %b, %Y') if row.updated_at else '-'  # Format the created_at field      
        if column == 'status':
            status = row.status
            today = date.today()
            start_date = row.start_date
            end_date = row.end_date
            remaining_days = None
            days_until_start = None

            status_info = {'status':row.status, 'remaining_days':remaining_days, 'days_until_start':days_until_start}

            if status == 'Approved':
                if today < start_date:
                    status_info['days_until_start'] = (start_date - today).days 
                elif start_date <= today <= end_date:
                    status_info['remaining_days'] = (end_date - today).days 
            return status_info
        if column == 'start_date':
            return row.start_date.strftime('%d %b, %Y')
        
        if column == 'end_date':
            return row.end_date.strftime('%d %b, %Y')
        
        if column == 'requested_days':
           return row.requested_days
        
        if column == 'id':
            return row.id
        
        if column == 'employee':
            return f"{row.employee.first_name} {row.employee.last_name}"
        
        return super().render_column(row, column)
      
    def get_initial_queryset(self):
        return LeaveRequest.objects.all()

    def filter_queryset(self, qs):
        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(employee__first_name__icontains=search) |
                Q(employee__last_name__icontains=search) |
                Q(leave_type__name__icontains=search) |
                Q(status__icontains=search)
            )
                # Additional filters for employee and leave type
        employee_id = self.request.GET.get('employee', None)
        leave_type_id = self.request.GET.get('leave_type', None)
        status = self.request.GET.get('status', None)

        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        
        if leave_type_id:
            qs = qs.filter(leave_type_id=leave_type_id)
        
        if status:
            qs = qs.filter(status=status)

        return qs

class LeaveRequestCreateView(LoginRequiredMixin, CreateView):
    model = LeaveRequest
    form_class = LeaveRequestForm
    template_name = 'hr/leave/leave_request_form.html'
    success_url = reverse_lazy('leave-request-list')

    def leave_balance(self):
        leave_balance_id = self.kwargs['pk']
        record = LeaveBalance.objects.get(pk=leave_balance_id)
        return record

    def get_initial(self):
        # Pre-populate initial values
        leave_balance = self.leave_balance()
        return {
            'employee': leave_balance.employee,
            'leave_type': leave_balance.leave_type,
            'days_requested': leave_balance.remaining_days,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass additional context variables for template
        leave_balance = self.leave_balance()
   
        context['employee'] = leave_balance.employee
        context['leave_type'] = leave_balance.leave_type
        context['remaining_days'] = leave_balance.remaining_days()
        context['title'] = f"{leave_balance.leave_type} request for {leave_balance.employee}"
        return context

    def get_form_kwargs(self):
        # Pass the remaining days to the form for validation
        kwargs = super().get_form_kwargs()

        leave_balance = self.leave_balance()
        kwargs['remaining_days'] = leave_balance.remaining_days()  # Pass remaining days to the form
        return kwargs

    def form_valid(self, form):
        start_date = form.cleaned_data['start_date']
        days_requested = form.cleaned_data['days_requested']
        status = form.cleaned_data['status']
        # Check for existing pending leave request and raise an error
        leave_balance = self.leave_balance()

        if form.instance.status == 'Pending':
            if LeaveRequest.objects.filter(status='Pending', employee=leave_balance.employee).exists():
                form.add_error("status", "Sorry, there is an existing pending leave request for same staff")
                return self.form_invalid(form)
        
        # Calculate end date, excluding weekends and public holidays
        end_date = calculate_end_date(start_date, days_requested)

        # Set end_date, employee & leave_type
        form.instance.end_date = end_date
        form.instance.employee = leave_balance.employee
        form.instance.leave_type = leave_balance.leave_type

        if status == 'Pending':
            None # send a message/sms request is  processed
        elif status == 'Approved':
            None # send message/sms request has being approved
        return super().form_valid(form)

class LeaveRequestUpdateView(LoginRequiredMixin, UpdateView):
    model = LeaveRequest
    form_class = LeaveRequestForm
    template_name = 'hr/leave/leave_request_form.html'
    success_url = reverse_lazy('leave-request-list')


    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        leave_request = self.get_object()
        employee_name = f"{leave_request.employee.first_name} {leave_request.employee.last_name}"
        context['title'] = f"Update {employee_name} leave request"
        leave_balance = LeaveBalance.objects.get(employee=leave_request.employee, leave_type=leave_request.leave_type)

        # Pass additional context variables for template
        context['employee'] = leave_balance.employee
        context['leave_type'] = leave_balance.leave_type
        context['remaining_days'] = leave_balance.remaining_days()

        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        leave_request = self.get_object()
        leave_balance = get_object_or_404(LeaveBalance, employee=leave_request.employee, leave_type=leave_request.leave_type)
        kwargs.update({'remaining_days': leave_balance.remaining_days()})
        return kwargs
    
    def form_valid(self, form):
        start_date = form.cleaned_data['start_date']
        days_requested = form.cleaned_data['days_requested']
        status = form.cleaned_data['status']
        # Calculate end date again(it may change on update), excluding weekends and public holidays
        end_date = calculate_end_date(start_date, days_requested)

        # Set end_date, employee & leave_type
        form.instance.end_date = end_date

        # trigger sms notification
        if status == 'Rejected':
            None
        elif status == 'Approved':
            None

        context = self.get_context_data()
        leave_type = context['leave_type']
        employee = context['employee']
        messages.success(self.request, f"{employee} {leave_type.name} successfully updated")
        return super().form_valid(form)  
    
class PublicHolidayListView(LoginRequiredMixin, ListView):
    model = PublicHoliday
    template_name = 'hr/leave/holiday_list.html'
    context_object_name = 'holiday_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Public Holidays'
        return context

class PublicHolidayCreateView(LoginRequiredMixin, CreateView):
    model = PublicHoliday
    template_name = 'hr/leave/holiday_form.html'
    fields = ['name', 'date']
    success_url = reverse_lazy('holiday-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Public Holiday'
        return context
    
    def get_form(self, *args, **kwargs):
        form =  super().get_form(*args, **kwargs)
        form.fields['date'].widget = forms.DateInput(attrs={'type':'date'})
        return form
    
    def form_valid(self, form):
        date = form.cleaned_data['date']

        if date.year != get_current_year():
            form.add_error('date', "Date must fall within this year")
            return self.form_invalid(form)

        messages.success(self.request, f"{form.instance.name} successfully added")
        return super().form_valid(form)

class PublicHolidayUpdateView(LoginRequiredMixin, UpdateView):
    model = PublicHoliday
    template_name = 'hr/leave/holiday_form.html'
    fields = ['name', 'date']
    success_url = reverse_lazy('holiday-list')
   
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Update {self.get_object().name}'
        return context 
    
    def form_valid(self, form):
        date = form.cleaned_data['date']
        if date.year != get_current_year():
            form.add_error('date', "Date must fall within this year")
            return self.form_invalid(form)
         
        messages.success(self.request, f"{form.instance.name} successfully updated")
        return super().form_valid(form)
    
        

def delete_holiday(request, pk):
 holiday = PublicHoliday.objects.get(id=pk)
 if request.method == "POST":
        holiday.delete()
        messages.success(request, f"{holiday} was deleted successfully")
        return redirect('holiday-list')

 return render(request, 'core/delete.html', {'obj':holiday, 'title': f'Delete {holiday}?'})
 