from django.urls import path
from .views import *


urlpatterns = [
     path('', SaleListView.as_view(), name='sale-list'),
]
