from django.db import models 
from django.core.exceptions import ValidationError
from django.db.models import F, Index
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import re

class Warehouse(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Under Maintenance'),
        ('closed', 'Temporarily Closed')
    ]

    # Existing fields
    warehouse_name = models.CharField(max_length=255, verbose_name="Warehouse Name", unique=True)
    manager = models.ForeignKey('hr.Employee', on_delete=models.CASCADE, null=True, blank=True, related_name="warehouses")
    
    # Contact Information
    phone = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    
    # Location Details
    street = models.CharField(max_length=120, null=True)
    city = models.CharField(max_length=64, null=True)
    address = models.CharField(max_length=255, null=True, help_text="Can also be Digital or Postal code")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Operational Details
    open_time = models.TimeField(verbose_name="Opening Time")
    close_time = models.TimeField(verbose_name="Closing Time")
    operating_days = models.PositiveIntegerField(verbose_name="Number of Operating Days")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Capacity Details
    total_capacity = models.PositiveIntegerField(verbose_name="Total Capacity (m³)", null=True, blank=True)
    storage_area = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Storage Area (m²)", null=True, blank=True)
    number_of_docks = models.PositiveIntegerField(verbose_name="Number of Loading Docks", default=1)
    temperature_controlled = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            Index(fields=['warehouse_name']),
            Index(fields=['manager']),
            Index(fields=['status']),
        ]

    def __str__(self):
        return self.warehouse_name
    
    def clean(self):
        super().clean()
        # Ensure open time and close time aren't the same
        if self.open_time and self.close_time and self.open_time == self.close_time:
            raise ValidationError(_("Openning time cannot be the same as closing time"))
        
        # Ensure operating days is greater than 0 but not more than 7
        if self.operating_days and (self.operating_days < 0 or self.operating_days > 7):
            raise ValidationError(_("Operating days must be 1 to 7 working days"))

        # validate phone number 
        if self.phone:
            self.clean_phone()

    def clean_phone(self):
        cleaned_number = ''.join(filter(str.isdigit, self.phone))
        if not re.match(r'^0(23|24|25|53|54|55|59|27|57|26|56|28|20|50)\d{7}$', cleaned_number):
            raise ValidationError(_("Invalid phone number, please use a valid Ghanaian phone number"))

class Transfer(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('transit', 'Transit'),
        ('partial', 'Partially Received'),
        ('received', 'Fully Received'),
        ('cancelled', 'Cancelled')
    ]
    source = models.ForeignKey('Warehouse', on_delete=models.CASCADE, related_name="source_warehouses", verbose_name="Source Warehouse")
    destination = models.ForeignKey('Warehouse', on_delete=models.CASCADE, related_name="destination_warehouses", verbose_name="Destination Warehouse")
    quantity = models.PositiveIntegerField(verbose_name="Transfer Quantity")
    transfer_date = models.DateField(verbose_name="Transfer Date")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    product = models.ForeignKey('operations.Product', on_delete=models.CASCADE, related_name="transfers")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            Index(fields=['source']),
            Index(fields=['destination']),
            Index(fields=['product']),
            Index(fields=['status']),
        ]

    def __str__(self):
        return f"Transfer from {self.source} To {self.destination}"
    
    def clean(self):
        super().clean()

        # Ensure that origin and destination are not the same
        if self.source == self.destination:
            raise ValidationError(_("source warehouse cannot be same as destination warehouse"))

        # Validation integrity for product quantity at source aganist transfer quantity
        # use related name of origin to get record of Inventory using source and product as lookup
        from .operations import Inventory
        try:
            source_inventory = Inventory.objects.get(product=self.product, warehouse=self.source)
            if self.quantity > source_inventory.quantity:
                raise ValidationError(_(f"Insufficient stock. Available: {source_inventory.quantity} {self.product}"))

        except Inventory.DoesNotExist:
            raise ValidationError(_(f"Product {self.product} not available in source warehouse"))   
    
        # if destination warehouse does not have product, transfer must be treated as open balance
        if not Inventory.objects.filter(warehouse=self.destination, product=self.product).exists():
            raise ValidationError(_(f"Product {self.product} not set up in destination warehouse. Please create inventory record first"))
    
    def save(self, *args, **kwargs):
        from .operations import Inventory
        if self.status == 'received':
            # reduce quantity of product at source
            source_inventory = Inventory.objects.get(product=self.product, warehouse=self.source)
            source_inventory.quantity -= self.quantity
            source_inventory.save()

            # increase quantity of product at destination
            dest_inventory =  Inventory.objects.get(product=self.product, warehouse=self.destination)
            dest_inventory.quantity += self.quantity
            dest_inventory.save()

        super().save(*args, **kwargs)

class Van(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('maintenance', 'Under Maintenance'),
        ('repair', 'Under Repair'),
        ('inactive', 'Inactive')
    ]

    # Basic Details
    make = models.CharField(max_length=100, verbose_name="Make")
    model = models.CharField(max_length=100, verbose_name="Model")
    year = models.PositiveIntegerField(verbose_name="Year")
    plate_number = models.CharField(max_length=20, unique=True, verbose_name="Plate Number")
    vin = models.CharField(max_length=17, unique=True, verbose_name="VIN")

    # Specifications
    capacity_weight = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Capacity (kg)")
    cargo_length = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Cargo Length (m)")
    cargo_width = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Cargo Width (m)")
    cargo_height = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Cargo Height (m)")

    # Operational Details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    assigned_driver = models.ForeignKey('hr.Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_vans')
    current_mileage = models.PositiveIntegerField(verbose_name="Current Mileage")

    # Documentation
    registration_expiry = models.DateField(verbose_name="Registration Expiry Date")
    insurance_expiry = models.DateField(verbose_name="Insurance Expiry Date")
    last_maintenance = models.ForeignKey('VanMaintenance', on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
        verbose_name="Last Maintenance"
    )
    next_maintenance = models.DateField(null=True, blank=True, verbose_name="Next Maintenance Date")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Van"
        verbose_name_plural = "Vans"
        ordering = ['-created_at']
        indexes = [
            Index(fields=['plate_number']),
            Index(fields=['vin']),
            Index(fields=['status']),
            Index(fields=['assigned_driver']),
        ]

    def __str__(self):
        return f"{self.year} {self.make} {self.model} ({self.plate_number})"

    def clean(self):
        super().clean()
        
        # Ensure registration isn't expired
        if self.registration_expiry < timezone.now().date():
            raise ValidationError(_("Registration has expired"))

        # Ensure insurance isn't expired
        if self.insurance_expiry < timezone.now().date():
            raise ValidationError(_("Insurance has expired"))

        # Validate next maintenance date
        if self.next_maintenance and self.last_maintenance:
            if self.next_maintenance <= self.last_maintenance:
                raise ValidationError(_("Next maintenance date must be after last maintenance date"))
            
        # Validate capacity

class VanMaintenance(models.Model):
    MAINTENANCE_TYPE = [
        ('routine', 'Routine Service'),
        ('repair', 'Repair'),
        ('inspection', 'Inspection'),
        ('emergency', 'Emergency Repair')
    ]
    
    van = models.ForeignKey('Van', on_delete=models.CASCADE, related_name='maintenance_records')
    maintenance_date = models.DateField(verbose_name="Maintenance Date")
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPE)
    description = models.TextField(verbose_name="Maintenance Description")
    mileage_at_service = models.PositiveIntegerField(null=True, blank=True, verbose_name="Mileage at Service")
    cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Maintenance Cost")
    service_provider = models.CharField(max_length=255, verbose_name="Service Provider")
    next_service_date = models.DateField(verbose_name="Next Service Date", null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    invoice_number = models.CharField(max_length=50, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-maintenance_date']

    def __str__(self):
        return f"{self.van.plate_number} - {self.maintenance_type} on {self.maintenance_date}"


# Logistics models
class DeliveryRoute(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Route Name")
    start_point = models.ForeignKey('Warehouse', on_delete=models.PROTECT, verbose_name="Start Point", related_name='route_starts')
    end_point = models.ForeignKey('Warehouse', on_delete=models.PROTECT, verbose_name="End Point", related_name='route_ends')
    distance = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Distance (km)")
    estimated_time = models.DurationField(verbose_name="Estimated Travel Time")
    description = models.TextField(null=True, blank=True)
    active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.start_point} to {self.end_point})"

    def clean(self):
        if self.start_point == self.end_point:
            raise ValidationError(_("Start and end points cannot be the same warehouse"))

class DeliverySchedule(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_transit', 'In Transit'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]

    van = models.ForeignKey('Van', on_delete=models.PROTECT, related_name='delivery_schedules')
    driver = models.ForeignKey('hr.Employee', on_delete=models.PROTECT, related_name='delivery_schedules')
    route = models.ForeignKey('DeliveryRoute', on_delete=models.PROTECT, related_name='schedules')
    departure_time = models.DateTimeField(verbose_name="Departure Time")
    estimated_arrival = models.DateTimeField(verbose_name="Estimated Arrival")
    actual_arrival = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-departure_time']

    def __str__(self):
        return f"{self.route.name} - {self.van.plate_number} - {self.departure_time}"

    def clean(self):
        if self.estimated_arrival <= self.departure_time:
            raise ValidationError(_("Estimated arrival must be after departure time"))
        
        if self.van.status != 'active':
            raise ValidationError(_("Selected van must be active"))
