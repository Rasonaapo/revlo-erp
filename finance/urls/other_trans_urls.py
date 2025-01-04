from django.urls import path

from ..views.other_trans_views import *

urlpatterns = [
     path('journal-transaction/', JournalListView.as_view(), name='journal-list'),
]
