from django.urls import path
from ..views.warehouse_views import *

urlpatterns = [
     path('', WarehouseListView.as_view(), name='customer-list')
]
