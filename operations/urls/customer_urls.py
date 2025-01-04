from django.urls import path
from ..views.customer_views import *

urlpatterns = [
     path('', CustomerListView.as_view(), name='customer-list')
]
