# In dronedelivery/models.py

from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point

class Location(gis_models.Model):
    name = models.CharField(max_length=100)
    coordinates = gis_models.PointField(geography=True, default=Point(0.0, 0.0))
    is_depot = models.BooleanField(default=False)
    address = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name

class Drone(models.Model):
    STATUS_CHOICES = [
        ('idle', 'Idle'),
        ('in_transit', 'In Transit'),
        ('charging', 'Charging'),
        ('maintenance', 'Maintenance'),
    ]
    
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='idle')
    battery_level = models.FloatField(default=100.0)  # percentage
    max_payload = models.FloatField(help_text="Maximum payload in grams")
    current_location = gis_models.PointField(geography=True, null=True, blank=True)
    last_maintenance = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

class DeliveryRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ]
    
    pickup_location = models.ForeignKey(Location, related_name='pickup_requests', on_delete=models.PROTECT)
    dropoff_location = models.ForeignKey(Location, related_name='dropoff_requests', on_delete=models.PROTECT)
    weight = models.FloatField(help_text="Weight in grams")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    assigned_drone = models.ForeignKey(Drone, on_delete=models.SET_NULL, null=True, blank=True)
    priority = models.IntegerField(default=1, help_text="Higher number = higher priority")
    
    # Calculated fields
    distance = models.FloatField(null=True, blank=True, help_text="Distance in meters")
    estimated_duration = models.FloatField(null=True, blank=True, help_text="Estimated duration in minutes")
    actual_duration = models.FloatField(null=True, blank=True, help_text="Actual duration in minutes")
    
    def __str__(self):
        return f"Delivery {self.id} ({self.get_status_display()})"

class Route(models.Model):
    delivery = models.OneToOneField(DeliveryRequest, on_delete=models.CASCADE, related_name='route')
    path = gis_models.LineStringField(geography=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Route for Delivery {self.delivery.id}"

class DroneTelemetry(models.Model):
    drone = models.ForeignKey(Drone, on_delete=models.CASCADE, related_name='telemetry')
    timestamp = models.DateTimeField(auto_now_add=True)
    location = gis_models.PointField(geography=True)
    battery_level = models.FloatField()
    speed = models.FloatField(help_text="Speed in m/s")
    altitude = models.FloatField(help_text="Altitude in meters")
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Telemetry for {self.drone.name} at {self.timestamp}"

class DeliveryMetrics(models.Model):
    date = models.DateField(unique=True)
    total_deliveries = models.IntegerField(default=0)
    successful_deliveries = models.IntegerField(default=0)
    average_delivery_time = models.FloatField(help_text="Average delivery time in minutes")
    average_cost_per_km = models.FloatField(help_text="Average cost per kilometer")
    total_distance = models.FloatField(help_text="Total distance covered in kilometers")
    
    def success_rate(self):
        return (self.successful_deliveries / self.total_deliveries * 100) if self.total_deliveries > 0 else 0
    
    def __str__(self):
        return f"Metrics for {self.date}"