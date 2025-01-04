from django.urls import path

from ..views.revenue_views import *

urlpatterns = [
     path('transactions/', RevenueListView.as_view(), name='revenue-list'),
]
