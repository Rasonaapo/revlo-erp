from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from operations.models.operations import Inventory, ProductCategory
from django_datatables_view.base_datatable_view import BaseDatatableView
from django.utils.html import escape
from datetime import date
from django.db.models import Q, Count
import json
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse


class InventoryListApiView(LoginRequiredMixin, BaseDatatableView):
    model = Inventory
    columns =  ['id', 'warehouse', 'product', 'quantity', 'min_stock_level', 'max_stock_level', 'reorder_level', 'created_at']

 

    def render_column(self, row, column):
        if column == 'warehouse':
            return row.warehouse.warehouse_name
        
        if column == 'product':
            return row.product.product_name
        
        if column == 'quantity':
            return row.quantity
        
        if column == 'reorder_level':
            return row.reorder_level
        
        if column == 'min_stock_level':
            return row.min_stock_level
        
        if column == 'max_stock_level':
            return row.max_stock_level
    
        if column == 'created_at':
            return row.created_at.strftime('%d %b, %Y')
        
        if column == 'id':
            return row.id
        
        return super().render_column(row, column)
    
    def get_initial_queryset(self):
        return Inventory.objects.all()
    
    def filter_queryset(self, qs):
        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(product__product_name__icontains=search) |
                Q(warehouse__warehouse_name__icontains=search)
            )
        return qs

class ProductCategoryListApiView(LoginRequiredMixin, BaseDatatableView):
    model = ProductCategory
    columns =  ['id', 'category_name', 'description', 'created_at']

    def render_column(self, row, column):
        if column == 'category_name':
            return row.category_name
        
        if column == 'description':
            # return first 30 chars if more than 30 else return all chars
            return row.description if len(row.description) <= 20 else row.description[:20] + '...'
        
        if column == 'created_at':
            return row.created_at.strftime('%d %b, %Y')
        
        if column == 'id':
            return row.id
        
        return super().render_column(row, column)
    
    def get_initial_queryset(self):
        return ProductCategory.objects.all()
    
    def filter_queryset(self, qs):
        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(category_name__icontains=search) |
                Q(description__icontains=search)
            )
        return qs