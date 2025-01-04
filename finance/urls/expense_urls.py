from django.urls import path

from ..views.expense_views import *

urlpatterns = [
     path('transactions/', ExpenseListView.as_view(), name='expense-list'),
]
