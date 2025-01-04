from django.contrib import admin
from .models import (
    SaleManTarget, Store, POS, Sale, SaleDetail, SaleDamage, Delivery, DeliveryItem
)

@admin.register(SaleManTarget)
class SaleManTargetAdmin(admin.ModelAdmin):
    list_display = ('sales_man', 'daily_target', 'weekly_target', 'monthly_target', 'created_at', 'updated_at')
    search_fields = ('sales_man__name',)
    list_filter = ('sales_man',)

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('store_name', 'warehouse', 'manager', 'phone', 'email', 'status', 'created_at', 'updated_at')
    search_fields = ('store_name', 'warehouse__warehouse_name', 'manager__name')
    list_filter = ('status', 'warehouse')

@admin.register(POS)
class POSAdmin(admin.ModelAdmin):
    list_display = ('pos_number', 'store', 'terminal_id', 'ip_address', 'status', 'last_transaction', 'created_at', 'updated_at')
    search_fields = ('pos_number', 'store__store_name', 'terminal_id')
    list_filter = ('status', 'store')

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('sale_number', 'pos', 'customer', 'salesman', 'sale_date', 'payment_method', 'total', 'created_at', 'updated_at')
    search_fields = ('sale_number', 'pos__pos_number', 'customer__company_name', 'salesman__name')
    list_filter = ('payment_method', 'sale_date')

@admin.register(SaleDetail)
class SaleDetailAdmin(admin.ModelAdmin):
    list_display = ('sale', 'product', 'quantity', 'unit_price', 'subtotal', 'created_at', 'updated_at')
    search_fields = ('sale__sale_number', 'product__product_name')
    list_filter = ('sale', 'product')

@admin.register(SaleDamage)
class SaleDamageAdmin(admin.ModelAdmin):
    list_display = ('sale', 'product', 'quantity', 'reason', 'description', 'date_reported', 'created_at', 'updated_at')
    search_fields = ('sale__sale_number', 'product__product_name')
    list_filter = ('reason', 'date_reported')

@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('delivery_note_number', 'sale', 'schedule', 'delivery_status', 
                   'recipient_name', 'recipient_phone', 'created_at')
    search_fields = ('delivery_note_number', 'recipient_name', 'recipient_phone', 
                    'sale__sale_number')
    list_filter = ('delivery_status', 'created_at', 'schedule__route')

@admin.register(DeliveryItem)
class DeliveryItemAdmin(admin.ModelAdmin):
    list_display = ('delivery', 'sale_detail', 'quantity_to_deliver', 
                   'quantity_delivered', 'quantity_returned', 'status')
    search_fields = ('delivery__delivery_note_number', 
                    'sale_detail__product__product_name')
    list_filter = ('status', 'delivery__delivery_status')