from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView


# Create your views here.
class RevenueListView(LoginRequiredMixin, DetailView):
    pass 