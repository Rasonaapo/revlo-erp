from django.urls import path
from ..views.inventory_views import *

urlpatterns = [
     path('', InventoryListView.as_view(), name='inventory-list')
]
