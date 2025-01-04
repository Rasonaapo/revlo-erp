from django.urls import path
from ..views.supplier_views import *

urlpatterns = [
     path('', SupplierListView.as_view(), name='customer-list')
]
