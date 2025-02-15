from django.contrib import admin
from .models import (
    ProductCategory, Product, ProductUnit, UnitType, Inventory, Customer, Supplier,
    PurchaseOrder, PurchaseOrderDetail, InventoryDamage, Transfer,
    Van, VanMaintenance, DeliveryRoute, DeliverySchedule
)

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name', 'description')
    search_fields = ('category_name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'product_category', 'brand', 'is_composite')
    search_fields = ('product_name', 'category__category_name')
    list_filter = ('product_category', 'is_composite',)

@admin.register(UnitType)  # Add this
class UnitTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(ProductUnit)  # Add this
class ProductUnitAdmin(admin.ModelAdmin):
    list_display = ('product', 'unit_type', 'barcode', 'quantity_per_unit', 'cost_price', 'sale_price')
    search_fields = ('product__product_name', 'barcode')
    list_filter = ('unit_type', 'is_purchasable', 'is_sellable')

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('warehouse', 'get_product_name', 'get_unit_type', 'quantity', 'min_stock_level', 'max_stock_level')
    search_fields = ('warehouse__warehouse_name', 'product_unit__product__product_name')
    list_filter = ('warehouse', 'product_unit__product')


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'contact_person', 'contact_phone', 'contact_email', 'credit_limit', 'current_balance')
    search_fields = ('company_name', 'contact_person')
    list_filter = ('company_name',)

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'contact_person', 'contact_phone', 'contact_email', 'current_balance')
    search_fields = ('company_name', 'contact_person')
    list_filter = ('company_name',)

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('po_number', 'supplier', 'order_date', 'expected_date', 'status', 'total')
    search_fields = ('po_number', 'supplier__company_name')
    list_filter = ('status', 'supplier')

@admin.register(PurchaseOrderDetail)
class PurchaseOrderDetailAdmin(admin.ModelAdmin):
    list_display = ('purchase_order', 'product', 'quantity_ordered', 'quantity_received', 'unit_price', 'subtotal')
    search_fields = ('purchase_order__po_number', 'product__product_name')
    list_filter = ('purchase_order', 'product')

@admin.register(InventoryDamage)
class InventoryDamageAdmin(admin.ModelAdmin):
    list_display = ('inventory', 'quantity', 'reason', 'description', 'date_reported')
    search_fields = ('inventory__product__product_name', 'inventory__warehouse__warehouse_name')
    list_filter = ('reason', 'date_reported')

@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ('source', 'destination', 'product', 'quantity', 'transfer_date', 'status')
    search_fields = ('source__warehouse_name', 'destination__warehouse_name', 'product__product_name')
    list_filter = ('status', 'transfer_date')

@admin.register(Van)
class VanAdmin(admin.ModelAdmin):
    list_display = ('make', 'model', 'year', 'plate_number', 'vin', 'status', 'current_mileage')
    search_fields = ('make', 'model', 'plate_number', 'vin')
    list_filter = ('status', 'year')

@admin.register(VanMaintenance)
class VanMaintenanceAdmin(admin.ModelAdmin):
    list_display = ('van', 'maintenance_date', 'maintenance_type', 'mileage_at_service', 'cost', 'service_provider', 'next_service_date')
    search_fields = ('van__plate_number', 'service_provider')
    list_filter = ('maintenance_type', 'maintenance_date')

@admin.register(DeliveryRoute)
class DeliveryRouteAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_point', 'end_point', 'distance', 'estimated_time', 'active')
    search_fields = ('name', 'start_point__warehouse_name', 'end_point__warehouse_name')
    list_filter = ('active', 'start_point', 'end_point')

@admin.register(DeliverySchedule)
class DeliveryScheduleAdmin(admin.ModelAdmin):
    list_display = ('route', 'van', 'driver', 'departure_time', 'estimated_arrival', 'status')
    search_fields = ('route__name', 'van__plate_number', 'driver__name')
    list_filter = ('status', 'departure_time', 'route')
    date_hierarchy = 'departure_time'