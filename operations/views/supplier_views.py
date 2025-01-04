from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView

class SupplierListView(LoginRequiredMixin, ListView):
    pass