from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView

class WarehouseListView(LoginRequiredMixin, ListView):
    pass