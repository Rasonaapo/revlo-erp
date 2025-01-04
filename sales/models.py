from django.db import models
from decimal import Decimal
from django.db.models import Index
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import re
from operations.models import Warehouse

class SaleManTarget(models.Model):
    sales_man = models.ForeignKey('hr.Employee', on_delete=models.CASCADE, related_name="sale_targets", verbose_name="Sales Man")
    daily_target = models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Daily Target")
    weekly_target = models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Weekly Target", help_text="Becomes necessary as some sales men may work for entire 7 days while certain days may be omitted for some")
    monthly_target = models.DecimalField(decimal_places=2, null=True, max_digits=10, editable=False, verbose_name="Monthly Target")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural  = "Sales Man Targets"
        indexes = [
            Index(fields=['sales_man']),
        ]

    def clean(self): 
        super().clean()
        
        # Ensure weekly target if set does not exceed sales target
        if self.weekly_target and self.daily_target and self.daily_target >= self.weekly_target:
            raise ValidationError(_("Daily target must be less than weekly target"))
class Store(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('renovation', 'Under Renovation'),
        ('closed', 'Temporarily Closed')
    ]

    store_name = models.CharField(max_length=255, unique=True)
    warehouse = models.ForeignKey('operations.Warehouse', on_delete=models.PROTECT, related_name='stores')
    manager = models.ForeignKey('hr.Employee', on_delete=models.SET_NULL, null=True, related_name='managed_stores')
    
    # Location & Contact
    address = models.TextField()
    phone = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(blank=True, null=True)
    
    # Operations
    open_time = models.TimeField(verbose_name="Opening Time")
    close_time = models.TimeField(verbose_name="Closing Time")
    operating_days = models.PositiveIntegerField(verbose_name="Operating Days", help_text="Number of operating days per week")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['store_name']
        indexes = [
            Index(fields=['store_name']),
            Index(fields=['warehouse']),
            Index(fields=['manager']),
        ]

    def __str__(self):
        return self.store_name
    

    def clean(self):
        super().clean()
        # Ensure open time and close time aren't the same
        if self.open_time and self.close_time and self.open_time == self.close_time:
            raise ValidationError(_("Openning time cannot be the same as closing time"))
        
        # Ensure operating days is greater than 0 but not more than 7
        if self.operating_days and (self.operating_days < 0 or self.operating_days > 7):
            raise ValidationError(_("Operating days must be 1 to 7 working days"))

        # validate phone number to be ghanaian numbers
        if self.phone:
            self.clean_phone()

    def clean_phone(self):
        cleaned_number = ''.join(filter(str.isdigit, self.phone))
        if not re.match(r'^0(23|24|25|53|54|55|59|27|57|26|56|28|20|50)\d{7}$', cleaned_number):
            raise ValidationError(_("Invalid phone number, please use a valid Ghanaian phone number"))
    
class POS(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Under Maintenance')
    ]

    pos_number = models.CharField(max_length=50, unique=True, editable=False)
    store = models.ForeignKey('Store', on_delete=models.CASCADE, related_name='pos_terminals')    
    # Hardware Details
    terminal_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    printer_name = models.CharField(max_length=100, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    last_transaction = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "POS"
        verbose_name_plural = "POS Terminals"
        ordering = ['store', 'pos_number']
        indexes = [
            Index(fields=['pos_number']),
            Index(fields=['store']),
        ]

    def __str__(self):
        return f"{self.store.store_name} - {self.pos_number}"

    def save(self, *args, **kwargs):
        #auto generate POS number
        if not self.pos_number:
            last_pos = POS.objects.filter(store=self.store).order_by('-id').first()
            next_number = 1 if not last_pos else int(last_pos.pos_number.split('-')[-1]) + 1
            self.pos_number = f"{self.store.store_name[:3].upper()}-POS{next_number:03d}"
        super().save(*args, **kwargs)
    
    def clean(self):
        super().clean()
        if self.ip_address:
            self.clean_ip_address()
    
    # write a clean_ip_address()
    def clean_ip_address(self):
        if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', self.ip_address):
            raise ValidationError(_("Invalid IP address format"))


class Sale(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('momo', 'Mobile Money'),
        ('split', 'Split Payment'),
    ]
    
    sale_number = models.CharField(max_length=50, unique=True, editable=False)
    pos = models.ForeignKey(POS, on_delete=models.PROTECT, related_name='sales')
    customer = models.ForeignKey('operations.Customer', on_delete=models.PROTECT, null=True, blank=True)
    salesman = models.ForeignKey('hr.Employee', on_delete=models.PROTECT, related_name='sales', null=True, blank=True)
    
    # Sale Details
    sale_date = models.DateTimeField(default=timezone.now)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    getfund = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    covid_levy = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    nhil = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    vat = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Payment Details
    amount_tendered = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    change_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            Index(fields=['sale_number']),
            Index(fields=['pos']),
            Index(fields=['customer']),
            Index(fields=['salesman']),
            Index(fields=['sale_date']),
        ]

    def save(self, *args, **kwargs):
        if not self.sale_number:
            last_sale = Sale.objects.filter(pos=self.pos).order_by('-id').first()
            next_number = 1 if not last_sale else int(last_sale.sale_number.split('-')[-1]) + 1
            self.sale_number = f"{self.pos.store.store_name[:3].upper()}-{self.pos.pos_number}-{next_number:06d}"
        super().save(*args, **kwargs)

class SaleDetail(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('operations.Product', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            Index(fields=['sale']),
            Index(fields=['product']),
        ]

    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        
        # Update Sale totals
        sale = self.sale
        details = sale.items.all()
        sale.subtotal = sum(detail.subtotal for detail in details)
        sale.tax = sale.subtotal * Decimal('0.15')  # Assuming 15% tax
        sale.total = sale.subtotal + sale.tax - sale.discount
        sale.save()

class SaleDamage(models.Model):
    DAMAGE_REASONS = [
        ('expired', 'Expired'),
        ('broken', 'Broken/Physical Damage'),
        ('water', 'Water Damage'),
        ('temperature', 'Temperature Related'),
        ('pest', 'Pest Damage'),
        ('quality', 'Quality Issues'),
        ('other', 'Other')
    ]

    sale = models.ForeignKey('Sale', on_delete=models.PROTECT, related_name='damages')
    product = models.ForeignKey('operations.Product', on_delete=models.PROTECT, related_name='sale_damages')
    quantity = models.PositiveIntegerField(verbose_name="Damaged Quantity")
    reason = models.CharField(max_length=20, choices=DAMAGE_REASONS)
    description = models.TextField(help_text="Detailed description of damage")
    date_reported = models.DateField(default=timezone.now)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_reported']
        indexes = [
            Index(fields=['sale']),
            Index(fields=['product']),
            Index(fields=['date_reported']),
        ]

    def clean(self):
        # Ensure damage quantity is greater than zero
        if self.quantity <= 0:
            raise ValidationError(_("Damage quantity must be greater than zero"))

        # Ensure damage quantity is not more than sold quantity
        sale_detail = SaleDetail.objects.filter(sale=self.sale, product=self.product).first()
        if sale_detail and self.quantity > sale_detail.quantity:
            raise ValidationError(_("Damage quantity cannot exceed sold quantity"))

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.product_name} - {self.quantity} units damaged on {self.date_reported}"

class Delivery(models.Model):
    DELIVERY_STATUS = [
        ('pending', 'Pending'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('partial', 'Partially Delivered'),
        ('failed', 'Failed')
    ]

    sale = models.ForeignKey('Sale', on_delete=models.PROTECT)
    schedule = models.ForeignKey('operations.DeliverySchedule', on_delete=models.PROTECT)
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS, verbose_name="Delivery Status", default='pending')
    delivery_note_number = models.CharField(max_length=50, unique=True, verbose_name="Delivery Note Number")
    delivery_address = models.TextField(verbose_name="Delivery Address")
    recipient_name = models.CharField(max_length=100, verbose_name="Recipient Name")
    recipient_phone = models.CharField(max_length=20, verbose_name="Recipient Phone")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"DN-{self.delivery_note_number} ({self.get_delivery_status_display()})"

class DeliveryItem(models.Model):
    ITEM_STATUS = [
        ('pending', 'Pending'),
        ('packed', 'Packed'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('returned', 'Returned'),
        ('damaged', 'Damaged in Transit')
    ]

    delivery = models.ForeignKey('Delivery', on_delete=models.CASCADE, related_name='items')
    sale_detail = models.ForeignKey('SaleDetail', on_delete=models.PROTECT, verbose_name="Sale Item")
    quantity_to_deliver = models.PositiveIntegerField(verbose_name="Quantity to Deliver")
    quantity_delivered = models.PositiveIntegerField(default=0, verbose_name="Quantity Delivered")
    quantity_returned = models.PositiveIntegerField(default=0, verbose_name="Quantity Returned")
    status = models.CharField(max_length=20, choices=ITEM_STATUS, default='pending')
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['delivery']),
            models.Index(fields=['sale_detail']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.sale_detail.product.product_name} ({self.quantity_to_deliver})"

    def clean(self):
        # Ensure delivery quantity is less or eqaual to quantity sold
        if self.quantity_to_deliver > self.sale_detail.quantity:
            raise ValidationError(_("Delivery quantity cannot exceed sold quantity"))
        
        # Ensure delivered quantity is less or equal to quantity to deliver
        if self.quantity_delivered > self.quantity_to_deliver:
            raise ValidationError(_("Delivered quantity cannot exceed delivery quantity"))

        # Ensure quantity returned is less or equal to quantity delivered
        if self.quantity_returned > self.quantity_delivered:
            raise ValidationError(_("Returned quantity cannot exceed delivered quantity"))
    
