from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .warehouse import Warehouse
from django.utils import timezone
from decimal import Decimal

class ProductCategory(models.Model):
    category_name = models.CharField(max_length=255, unique=True, verbose_name="Category Name")
    description = models.TextField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Product Categories"
        indexes = [
            models.Index(fields=['category_name']),
        ]

    def __str__(self):
        return f"{self.category_name}"

class Product(models.Model):
    WEIGHT_UNITS = [
        ('g', 'Gram'),
        ('kg', 'Kilogram'),
        ('ml', 'Milliliter'),
        ('ltr', 'Liter'),
        ('oz', 'Ounce'),
        ('lb', 'Pound'),
    ]

    product_name = models.CharField(max_length=255, unique=True, verbose_name="Product Name")
    barcode = models.CharField(max_length=255, unique=True, null=True)
    description = models.TextField(null=True)
    product_category = models.ForeignKey('ProductCategory', on_delete=models.CASCADE, related_name="products", verbose_name="Product Category")
    variant = models.CharField(max_length=120, null=True, blank=True, verbose_name="Product Variant")
    brand = models.CharField(max_length=120, null=True, blank=True, help_text="Brand or Manufacturer of the product", verbose_name="Brand")
    weight = models.FloatField(null=True, blank=True, verbose_name="Weight")
    weight_unit = models.CharField(max_length=3,  choices=WEIGHT_UNITS, default='kg', verbose_name="Weight Unit")
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cost Price", help_text="Cost price per unit")
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Sale Price", help_text="Selling price per unit")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['product_name']),
            models.Index(fields=['product_category']),
            models.Index(fields=['weight', 'weight_unit']),
        ]

    def __str__(self):
        return f"{self.weight}{self.get_weight_unit_display()} {self.product_name}"
    
    def clean(self):
        super().clean()

        # Cost price and sale price must be positive numbers
        if self.cost_price <= 0:
            raise ValidationError(_("Cost price must be a positive number"))
        if self.sale_price <= 0:
            raise ValidationError(_("Sale price must be a positive number"))

        # Sale price must be greater than cost price
        if self.cost_price >= self.sale_price:
            raise ValidationError(_("Cost price must always be lesser than sale price"))

        # Weight must be a positive number
        if self.weight is not None and self.weight <= 0:
            raise ValidationError(_("Weight must be a positive number"))

class Inventory(models.Model):
    warehouse = models.ForeignKey('operations.Warehouse', on_delete=models.CASCADE, related_name="inventories")
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name="inventories")
    min_stock_level = models.PositiveIntegerField(verbose_name="Minimum Stock Level")
    max_stock_level = models.PositiveIntegerField(verbose_name="Maximum Stock Level")
    reorder_level = models.PositiveIntegerField(verbose_name="Reorder Level")
    quantity = models.PositiveIntegerField(default=0, verbose_name="Available Quantity")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('warehouse', 'product')
        verbose_name_plural = "Inventories"
        indexes = [
            models.Index(fields=['warehouse']),
            models.Index(fields=['product']),
        ]

    def clean(self):
        super().clean()

        # validate min and max stock levels integrity
        if self.min_stock_level >= self.max_stock_level:
            raise ValidationError(_("Minimum stock level must be lesser than Maximum stock level"))
        
        # Ensure reorder level is somewhere between min and max or equal max
        if self.min_stock_level >= self.reorder_level or self.reorder_level > self.max_stock_level:
            raise ValidationError(_("Reorder level must be between min & max stock levels or at most equal to max stock level"))

    def get_inventory_status(self):
        """Returns inventory status with appropriate UI theme class"""
        if self.quantity <= self.min_stock_level:
            return {
                'status': 'Critical Stock Level',
                'theme': 'danger',
                'message': f'Stock is below minimum ({self.min_stock_level} units)'
            }
        elif self.quantity <= self.reorder_level:
            return {
                'status': 'Reorder Required',
                'theme': 'warning',
                'message': f'Stock is below reorder point ({self.reorder_level} units)'
            }
        elif self.quantity >= self.max_stock_level:
            return {
                'status': 'Overstocked',
                'theme': 'info',
                'message': f'Stock exceeds maximum ({self.max_stock_level} units)'
            }
        else:
            return {
                'status': 'Optimal',
                'theme': 'success',
                'message': 'Stock levels are optimal'
            }

class Customer(models.Model):
    # Company Details
    company_name = models.CharField(max_length=255, unique=True, verbose_name="Company Name")
    tax_number = models.CharField(max_length=50, null=True, blank=True, verbose_name="Tax Identification Number")
    
    # Contact Person
    contact_person = models.CharField(max_length=255, verbose_name="Contact Person")
    contact_position = models.CharField(max_length=100, null=True, blank=True)
    contact_phone = models.CharField(max_length=20, verbose_name="Phone Number")
    contact_email = models.EmailField(verbose_name="Email Address")
    
    # Company Contact Info
    company_phone = models.CharField(max_length=20, verbose_name="Company Phone")
    company_email = models.EmailField(verbose_name="Company Email")
    website = models.URLField(null=True, blank=True)
    
    # Address
    address = models.TextField(help_text="Digital address of the customer or Post Address")
    city = models.CharField(max_length=100)
    
    # Financial Details
    credit_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Credit limit for the customer", verbose_name="Credit Limit")
    current_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_terms = models.PositiveIntegerField(default=30, help_text="Payment terms in days", verbose_name="Payment Terms")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name.capitalize()

    class Meta:
        indexes = [
            models.Index(fields=['company_name']),
            models.Index(fields=['contact_person']),
        ]

    def clean(self):
        if self.current_balance > self.credit_limit:
            raise ValidationError(_("Current balance exceeds credit limit"))

class Supplier(models.Model):
    company_name = models.CharField(max_length=255, verbose_name="Company Name", unique=True)
    tax_number = models.CharField(max_length=50, verbose_name="Tax Identification Number", null=True, blank=True)   
    contact_person = models.CharField(max_length=255, verbose_name="Contact Person")
    contact_position = models.CharField(max_length=100, null=True, blank=True, verbose_name="Position")
    contact_phone = models.PositiveIntegerField(verbose_name="Phone Number" )
    contact_email = models.EmailField(null=True, blank=True, verbose_name="Email Address")
    company_phone = models.CharField(max_length=20, verbose_name="Company Phone")
    company_email = models.EmailField(verbose_name="Company Email")
    website = models.URLField(null=True, blank=True)
    address = models.TextField(help_text="Digital address of the supplier or Post Address")
    city = models.CharField(max_length=100, verbose_name="City", null=True)
    
    # Supply Details
    current_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_terms = models.PositiveIntegerField(default=30, help_text="Payment terms in days")
    lead_time = models.PositiveIntegerField(help_text="Average lead time in days")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['company_name']),
            models.Index(fields=['contact_person']),
        ]

    def clean(self):
        if self.current_balance < 0:
            raise ValidationError(_("Supplier balance cannot be negative"))
        
        if self.payment_terms <= 0:
            raise ValidationError(_("Payment terms must be a positive number"))
    
    def __str__(self):
        return self.company_name.capitalize()
    
class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('ordered', 'Ordered'),
        ('partial', 'Partially Received'),
        ('received', 'Fully Received'),
        ('cancelled', 'Cancelled')
    ]

    po_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(
        'Supplier', 
        on_delete=models.PROTECT,  # Prevent supplier deletion if POs exist
        related_name='purchase_orders',
        help_text="Supplier cannot be deleted while having purchase orders"
    )
    
    # Dates
    order_date = models.DateField(default=timezone.now)
    expected_date = models.DateField(null=True, blank=True)
    received_date = models.DateField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Financial fields
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['po_number']),
            models.Index(fields=['supplier']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.po_number} -  {self.supplier}"

    def save(self, *args, **kwargs):
        # auto generate PO number
        if not self.po_number:
            last_po = PurchaseOrder.objects.order_by('-id').first()
            next_number = 1 if not last_po else last_po.id + 1
            self.po_number = f'PO{next_number:06d}'
        
        # auto calculate expected date using supplier's lead time
        if not self.expected_date and self.supplier:
            self.expected_date = timezone.now().date() + timezone.timedelta(days=self.supplier.lead_time)
        
        super().save(*args, **kwargs)
    
    def clean(self):
        # Ensure goods are in warehouse before marking as received
        if self.status == 'received' and self.items.filter(warehouse__isnull=True).exists():
            raise ValidationError(_("Cannot mark as received when items haven't been assigned to warehouses"))

class PurchaseOrderDetail(models.Model):
    purchase_order = models.ForeignKey('PurchaseOrder', on_delete=models.CASCADE,related_name='items') # Delete details when PO is deleted
    product = models.ForeignKey('Product', on_delete=models.PROTECT,  related_name='purchase_order_items') # Prevent product deletion if in PO
    warehouse = models.ForeignKey('Warehouse', on_delete=models.PROTECT, blank=True, related_name='received_items')   # Prevent warehouse deletion if has items    
    quantity_ordered = models.PositiveIntegerField(verbose_name="Ordered Quantity")
    quantity_received = models.PositiveIntegerField(default=0, verbose_name="Received Quantity")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['purchase_order']),
            models.Index(fields=['product']),
        ]
    
    def save(self, *args, **kwargs):
        self.subtotal = self.quantity_ordered * self.unit_price
        super().save(*args, **kwargs)
        
        # Update PO totals
        po = self.purchase_order
        details = po.items.all()
        po.subtotal = sum(detail.subtotal for detail in details)
        po.tax = po.subtotal * po.tax
        po.total = po.subtotal + po.tax
        po.save()

    def clean(self):
        # Ensure received quantity is not negative
        if self.quantity_received > self.quantity_ordered:
            raise ValidationError(_("Received quantity cannot exceed ordered quantity"))
        
        # Ensure warehouse is assigned only when PO is being received
        if self.warehouse and self.purchase_order.status not in ['partial', 'received']:
            raise ValidationError(_("Cannot assign warehouse until PO is being received"))

class InventoryDamage(models.Model):
    DAMAGE_REASONS = [
        ('expired', 'Expired'),
        ('broken', 'Broken/Physical Damage'),
        ('water', 'Water Damage'),
        ('temperature', 'Temperature Related'),
        ('pest', 'Pest Damage'),
        ('quality', 'Quality Issues'),
        ('other', 'Other')
    ]

    inventory = models.ForeignKey('Inventory', on_delete=models.PROTECT,related_name='damages')
    quantity = models.PositiveIntegerField(verbose_name="Damaged Quantity")
    reason = models.CharField(max_length=20, choices=DAMAGE_REASONS)
    description = models.TextField(help_text="Detailed description of damage")
    date_reported = models.DateField(default=timezone.now)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_reported']
        indexes = [
            models.Index(fields=['inventory']),
            models.Index(fields=['date_reported']),
        ]

    def clean(self):
        # Ensure damage quantity is greater than zero
        if self.quantity <= 0:
            raise ValidationError(_("Damage quantity must be greater than zero"))

        # Ensure damage quantity is not more than available inventory 
        if self.quantity > self.inventory.quantity:
            raise ValidationError(_("Damage quantity cannot exceed available inventory"))

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
        # Update inventory quantity
        self.inventory.quantity -= self.quantity
        self.inventory.save()

    def __str__(self):
        return f"{self.inventory.product.product_name} - {self.quantity} units damaged on {self.date_reported}"