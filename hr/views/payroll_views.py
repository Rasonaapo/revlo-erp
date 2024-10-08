from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages

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


    