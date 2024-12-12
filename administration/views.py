from django.shortcuts import render
from .forms import MeetingForm, VendorForm, BusinessDocumentForm, BusinessDocumentUploadForm
from .models import Meeting, Attendance, Vendor, BusinessDocument, BusinessDocumentFile
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.views.generic import ListView, CreateView, UpdateView, DetailView 
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect, render
from django.db import transaction, DatabaseError, IntegrityError 
from django.http import JsonResponse
from django.db.models import Q, Count
from django_datatables_view.base_datatable_view import BaseDatatableView
from django.views.generic.edit import FormMixin


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

class VendorListView(LoginRequiredMixin, ListView):
    model = Vendor 
    template_name = 'administration/vendor/vendor_list.html'
    context_object_name = 'vendor_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Vendors'
        return context 

class VendorAPIView(LoginRequiredMixin, BaseDatatableView):
    model = Vendor 
    columns = ['id', 'name', 'phone_number', 'email', 'address', 'created_at']

    def render_column(self, row, column):
        if column == 'created_at':
            return row.created_at.strftime('%d %b, %Y')
        
        if column == 'phone_number':
           return row.format_phone_number() if row.phone_number else 'N/A'
        
        if column == 'address':
            address = row.address
            if address:
                return f"{address[:30]}..." if len(address) > 30 else address
            else:
                return 'N/A'
            
        return super().render_column(row, column)
    
    def filter_queryset(self, qs):
        search = self.request.GET.get('search[Value]', None)
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(phone_number__icontains=search) |
                Q(email__icontains=search) |
                Q(address__icontains=search) |
                Q(notes__icontains=search)
            )
        return qs
    
    def get_initial_queryset(self):
        return Vendor.objects.all()
    
class VendorCreateView(LoginRequiredMixin, CreateView):
    model = Vendor 
    template_name = 'administration/vendor/vendor_form.html'
    form_class = VendorForm 
    success_url = reverse_lazy('vendor-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Vendor'
        context['use_quill'] = True
        return context
    
    def form_valid(self, form):

        messages.success(self.request, f"Vendor [{form.instance.name}] successfully created")
        return super().form_valid(form)
    
class VendorUpdateView(LoginRequiredMixin, UpdateView):
    model = Vendor
    template_name = 'administration/vendor/vendor_form.html'
    form_class = VendorForm 
    success_url = reverse_lazy('vendor-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Update {self.get_object()}"
        context['use_quill'] = True
        return context
    
    def form_valid(self, form):

        messages.success(self.request, f"Vendor [{self.get_object().name}] successfully updated")
        return super().form_valid(form)

class VendorDetailView(LoginRequiredMixin, DetailView):
    model = Vendor 
    template_name = 'administration/vendor/vendor_detail.html'
    context_object_name = 'vendor' 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"{self.get_object()}"
        return context

def delete_vendor(request, pk):
    from django.http import Http404
    
    try:
        vendor = Vendor.objects.get(id=pk)
    except Vendor.DoesNotExist:
        raise Http404('Vendor Does Not Exist')
    
    if request.method == "POST":
        vendor.delete()
        messages.success(request, f"{vendor} successfully deleted")
        return redirect(reverse_lazy('vendor-list'))

    return render(request,  'core/delete.html', {'obj':vendor, 'title': f'Delete {vendor}?'})

class DocumentListView(LoginRequiredMixin, ListView):
    model = BusinessDocument 
    template_name = 'administration/business_docs/document_list.html'
    context_object_name = 'document_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Business Documents'
        return context 
    
class DocumentAPIView(LoginRequiredMixin, BaseDatatableView):
    model = BusinessDocument 
    columns = ['document_name', 'associated_entity', 'expiration_date', 'file_count', 'vendor', 'created_at', 'id']

    def render_column(self, row, column):
        if column == 'created_at':
            return row.created_at.strftime('%d %b, %Y')
        
        if column == 'vendor':
            return row.vendor.name if row.vendor else 'N/A'
        
        if column == 'expiration_date':
            return row.expiration_date.strftime('%d %b, %Y')
        
        if column == 'file_count':
            return row.file_count if row.file_count else 'N/A'
        
        return super().render_column(row, column)
    
    def get_initial_queryset(self):
        return BusinessDocument.objects.annotate(file_count=Count('document_files'))
    
    def filter_queryset(self, qs):
        search = self.request.GET.get('search[Value]')
        if search:
            qs = qs.filter(
                Q(document_name__icontains=search) |
                Q(associated_entity__icontains=search) |
                Q(documents__name__icontains=search) 
                
            )
        return qs

class DocumentCreateView(LoginRequiredMixin, CreateView):
    model = BusinessDocument
    template_name = 'administration/business_docs/document_form.html'
    form_class = BusinessDocumentForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Business Document'
        context['use_quill'] = True
        return context
    
    def form_valid(self, form):
        document = form.save()
        messages.success(self.request, f"{document.document_name} successfully created, proceed to upload files")
        return redirect(reverse_lazy('document-upload', kwargs={'pk':document.id}))
   

class DocumentUploadDetailView(LoginRequiredMixin, FormMixin, DetailView):
    model = BusinessDocument
    template_name = 'administration/business_docs/document_upload.html'
    context_object_name = 'business_document'
    form_class = BusinessDocumentUploadForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        business_document = self.get_object()
        context['title'] = f"Upload File(s) For {business_document}"
        # get files associated with this document
        context['document_files'] = BusinessDocumentFile.objects.filter(business_document=business_document)
        return context
    
    # process incoming files 
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        # get the form for processing
        form = self.get_form()
        if form.is_valid():
            # Do not commit until we've assign object to form instance..
            document_file = form.save(commit=False)
            document_file.business_document = self.object 
            # final commit
            document_file.save()

            messages.success(self.request, f"Document uploaded successfully")
            return redirect(reverse_lazy('document-upload', kwargs={'pk':self.object.pk}))
        else:
            return self.form_invalid(form)

    # Handle edge cases for invalid form submissions
    def form_invalid(self, form):
        """Handles invalid form submission"""
        context = self.get_context_data(form=form)
        messages.error(self.request, "Error: Document could not be uploaded. Please fix the errors below.")
        return self.render_to_response(context)

class DocumentUpdateView(LoginRequiredMixin, UpdateView):
    model = BusinessDocument
    template_name = 'administration/business_docs/document_form.html'
    context_object_name = 'business_document'
    form_class = BusinessDocumentForm
    success_url = reverse_lazy('document-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Update {self.get_object()}"
        context['use_quill'] = True
        return context 

    def form_valid(self, form):
        # check if the form has changed its initial data
        if  not form.has_changed():
            form.add_error(None, "No changes were detected in the form")
            return self.render_to_response(self.get_context_data(form=form))
        
        messages.success(self.request, f"{self.get_object()} successfully updated")
        return super().form_valid(form)

def delete_document(request, pk):
    from django.http import Http404

    try:
        document = BusinessDocument.objects.get(id=pk)
    except BusinessDocument.DoesNotExist:
        raise Http404('Business Document Does Not Exist')
    
    if request.method == "POST":
        document.delete()
        messages.success(request, f"{document} successfully deleted")
        return redirect(reverse_lazy('document-list'))
    
    return render(request,  'core/delete.html', {'obj':document, 'title': f'Delete {document}?'})

class DocumentDetailView(LoginRequiredMixin, DetailView):
    model = BusinessDocument 
    template_name = 'administration/business_docs/document_detail.html'
    context_object_name = 'document'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        document = self.get_object()
        context['title'] = f"{document} Detail"
        # get files associated with this business document...
        context['document_files'] = BusinessDocumentFile.objects.filter(business_document=document)
        return context
    
def delete_document_file(request, pk):
    from django.http import Http404
    try:
        doc_file = BusinessDocumentFile.objects.get(id=pk)
        document_id = doc_file.business_document.id
    except BusinessDocumentFile.DoesNotExist:
        raise Http404("Business Document File Does Not Exist")
    
    if request.method == "POST":
        doc_file.delete()

        messages.success(request, f"{doc_file} successfully deleted")
        return redirect(reverse_lazy('document-detail', kwargs={'pk':document_id}))
    
    return render(request,  'core/delete.html', {'obj':doc_file, 'title': f'Delete {doc_file}?'})
