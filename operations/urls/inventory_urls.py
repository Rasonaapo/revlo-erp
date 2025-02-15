from django.urls import path
from ..views.inventory_views import *
from ..views.inventory_json import *

urlpatterns = [
     path('', InventoryListView.as_view(), name='inventory-list'),
     path('api/', InventoryListApiView.as_view(), name='inventory-list-api'),
     path('categories/', ProductCategoryListView.as_view(), name='category-list'),
     path('categories/api/', ProductCategoryListApiView.as_view(), name='category-list-api'),
     path('categories/add/', ProductCategoryCreateView.as_view(), name='category-add'),
     path('categories/<int:pk>/update/', ProductCategoryUpdateView.as_view(), name='category-update'),
     path('categories/<int:pk>/delete/', delete_product_category, name='category-delete'),
     path('categories/<int:pk>/detail/', ProductCategoryDetailView.as_view(), name='category-detail'),
]
