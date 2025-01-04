from django.urls import path

from ..views.account_views import *

urlpatterns = [
     path('charts/', AccountListView.as_view(), name='account-list'),
]
