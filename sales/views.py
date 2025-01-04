from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
# Create your views here.

class SaleListView(LoginRequiredMixin, ListView):
    pass