from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView
from hr.models.payroll import Payroll, PayrollItem
from hr.models.employee import Employee

# Create your views here.
class EmployeeSSNITDetailView(LoginRequiredMixin, DetailView):
    pass 