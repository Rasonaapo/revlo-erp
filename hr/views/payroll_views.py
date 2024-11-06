from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from hr.models.payroll import *
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse


from hr.models.payroll import SalaryGrade

class SalaryGradeListView(LoginRequiredMixin, ListView):
    model = SalaryGrade
    template_name = 'hr/payroll/salarygrade_list.html'
    context_object_name = 'salarygrade_list'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.order_by('created_at')

        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Salary Grades'
        return context


class SalaryGradeCreateView(LoginRequiredMixin, CreateView):
    model = SalaryGrade
    template_name = 'hr/payroll/salarygrade_form.html'
    fields = ['grade', 'step', 'amount', 'currency']  
    success_url = reverse_lazy('salarygrade-list')  

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Salary Grade'
        return context

    
    def form_valid(self, form):
        messages.success(self.request, f'Salary grade [{form.instance.grade}] created successfully.')
        return super().form_valid(form)
    
class SalaryGradeUpdateView(LoginRequiredMixin, UpdateView):
    model = SalaryGrade
    template_name = 'hr/payroll/salarygrade_form.html'  
    fields = ['grade', 'step', 'amount', 'currency']  
    context_object_name = 'salary_grade'
    success_url = reverse_lazy('salarygrade-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Salary Grade'
        return context  

    def form_valid(self, form):
        # Any additional logic before saving can be added here
        messages.success(self.request, f'Salary grade [{form.instance.grade}] updated successfully.')
        return super().form_valid(form)
 
@login_required
def delete_salary_grade(request, pk):
    grade = SalaryGrade.objects.get(id=pk)

    if request.method == "POST":
        grade.delete()
        messages.success(request, f"{grade} successfully deleted")
        return redirect('salarygrade-list')
    
    return render(request, 'core/delete.html', {'obj':grade, 'title': f'Delete {grade}?'})

def setup_tax(request):
    context = {'title':'Tax Setup'}

    if request.method == "POST":
        with transaction.atomic():
        
            # clear the existence tax block for the current year if exist..
            current_year = timezone.now().year
            Tax.objects.filter(year=current_year).delete()
            
            existing_tax_blocks = Tax.objects.filter(year=timezone.now().year)
            if existing_tax_blocks:
                existing_tax_blocks.delete()
            
            # Get blocks and rates from the POST data
            blocks = request.POST.getlist('block[]')
            rates = request.POST.getlist('rate[]')
            errors = []

            tax_entries = []
            previous_rate = None

            try:
                for i in range(len(blocks)):
                    # We convert block and rate to float
                    block_amount = float(blocks[i]) if blocks[i] else None
                    rate_percent = float(rates[i]) if rates[i] else None

                    # Validate rate and ensure they ascend in order
                    # Skip the first block since rate is mostly 0 or 0
                    if i > 0 and previous_rate is not None and rate_percent < previous_rate:
                        errors.append(f"Rate for block {i + 1} must be higher than the previous block.")
        
                    previous_rate = rate_percent  # Update previous_rate for the next iteration
                    # Create tax instance and save later at once..
                    tax_entries.append(Tax(year=current_year, block=block_amount, rate=rate_percent))

                if errors:
                    return JsonResponse({'status':'fail', 'message':"<br>".join([error for error in errors])})
                
                # Create the tax entries now
                Tax.objects.bulk_create(tax_entries)
                return JsonResponse({'status': 'success', 'message': f"Tax setup successfully updated for the current year({current_year})"})


            except ValueError as e:
                # If any conversion fails, return an error response
                return JsonResponse({'status': 'fail', 'message': 'Invalid input. Please ensure all values are numbers.'})

    return render(request, 'hr/payroll/setup_tax.html', context)

