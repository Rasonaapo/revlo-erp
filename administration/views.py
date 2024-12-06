from django.shortcuts import render
from .forms import MeetingForm
from .models import Meeting, Attendance
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.views.generic import ListView, CreateView, UpdateView, DetailView 
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect, render
from django.db import transaction, DatabaseError, IntegrityError 
from django.http import JsonResponse
from django.db.models import Q
from django_datatables_view.base_datatable_view import BaseDatatableView

# Create your views here.

class MeetingAPIView(LoginRequiredMixin, BaseDatatableView):
    model = Meeting
    columns = ['id', 'subject', 'meeting_date', 'sms_date', 'location', 'attendees', 'status', 'created_at']

    def render_column(self, row, column):
        if column == 'meeting_date':
            return row.meeting_date.strftime('%d %b, %Y %I:%M %p')
        if column == 'sms_date':
            return row.sms_date.strftime('%d %b, %Y %I:%M %p')
        if column == 'created_at':
            return row.created_at.strftime('%d %b, %Y')
        if column == 'venue':
            return row.location
        if column == 'attendees':
            return len(row.get_meeting_employees())
        if column == 'status':
            status = row.status
            theme = 'danger'
            if status == 'pending':
                theme = 'info'
            elif status == 'on_going':
                theme = 'success'
   
            return {'theme':theme, 'status':row.get_status_display()}
                
        return super().render_column(row, column)
    
    def get_initial_queryset(self):
        return Meeting.objects.all()
    
    def filter_queryset(self, qs):
        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(subject__icontains=search) |
                Q(location__icontains=search) |
                Q(status__icontains=search)
            )
        return qs

class MeetingListView(LoginRequiredMixin, ListView):
    model = Meeting
    template_name = 'administration/meeting/meeting_list.html'
    context_object_name = 'meeting_list'

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        context['title'] = 'Meetings'
        return context

class MeetingCreateView(LoginRequiredMixin, CreateView):
    models = Meeting
    template_name = 'administration/meeting/meeting_form.html'
    form_class = MeetingForm
    success_url = reverse_lazy('meeting-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Meeting'
        return context
    
    def form_valid(self, form):
        meeting = form.save(commit=False)
        meeting.save() # Save to assign and ID to the meeting
        form.save_m2m()  # Save the many-to-many relationships (job, department, salary_grade)
        
        # Use get_meeting_employees to fetch relevant employees
        employees = meeting.get_meeting_employees()

        for employee in employees:
            Attendance.objects.create(
                    meeting=meeting,
                    employee=employee
                )
       
        messages.success(self.request, f"{meeting} was created successfully")
        return super().form_valid(form)
    
class MeetingUpdateView(LoginRequiredMixin, UpdateView):
    model = Meeting
    form_class = MeetingForm
    template_name = 'administration/meeting/meeting_form.html'
    context_object_name = 'meeting'
    success_url = reverse_lazy('meeting-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Update {self.get_object()}'
        return context
    
    def form_valid(self, form):
        meeting = form.save(commit=False)
        meeting.save()
        form.save_m2m()

        # Clear existing attendance records (important for UpdateView)
        Attendance.objects.filter(meeting=meeting).delete()

        employees = meeting.get_meeting_employees()
        for employee in employees:
            # Create attendance records for each relevant employee
            Attendance.objects.create(meeting=meeting, employee=employee)

        messages.success(self.request, f"{meeting} was updated successfully")
        return super().form_valid(form)

def delete_meeting(request, pk):
    meeting = Meeting.objects.get(id=pk)

    if request.method == 'POST':
        meeting.delete()
        messages.success(request, f"{meeting} was successfully deleted")
        return redirect('meeting-list')

    return render(request, 'core/delete.html', {'obj':meeting, 'title': f'Delete {meeting}?'})

class MeetingDetailView(LoginRequiredMixin, DetailView):
    model = Meeting
    context_object_name = 'meeting'
    template_name = 'administration/meeting/meeting_detail.html'

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)    
        meeting = self.get_object()  
        context['title'] = f"{meeting}"

        # fetch employees from attendance..
        context['attendees'] = Attendance.objects.filter(meeting=meeting).order_by('check_in_time') 

        # Determine if the meeting is past 
        return context  

def update_attendance(request, pk):
    meeting = Meeting.objects.get(id=pk)
    context = {'title': f"Mark Attendance For {meeting}"}

    # If status is on going or ended, fetch the employees and update their check in time 
    attendances = Attendance.objects.filter(meeting=meeting).order_by('check_in_time')
    if meeting.status == 'on_going' or meeting.status == 'ended':
        context.update({'attendances': attendances})
    
    if request.method == "POST":
        try:

            with transaction.atomic(): # Use transactions since we are doing DB operations in bulk
                # Loop over each attendance record from template and update if provided
                updates = 0
                for attendance in attendances:
                    check_in_time_key = f"check_in_time_{attendance.id}"  # Match the input name from the template   
                    check_in_time = request.POST.get(check_in_time_key) # Get the time value from the POST data
                    
                    try:
                        if check_in_time: 
                            attendance.check_in_time = check_in_time
                            attendance.save()
                            updates += 1
                    except DatabaseError as e:
                        return JsonResponse({'status':'fail', 'message':f"An error occured while updating {attendance.employee} record, try again later"})
                if updates:
                    label ="1 record was " if updates == 1 else f"{updates} records were "
                    return JsonResponse({'status':'success', 'message':f"{label} successfully updated"})
                else:
                    return JsonResponse({'status':'fail', 'message':"Nothing was updated"})

        except IntegrityError as e:
            return JsonResponse({'status': 'fail', 'message': 'An integrity error occurred. Please try again.'})

        except DatabaseError as e:
            return JsonResponse({'status': 'fail', 'message': 'A database error occurred. Please contact support if this continues.'})
         
    return render(request, 'administration/meeting/update_attendance.html', context)
