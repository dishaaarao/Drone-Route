from django.contrib import admin
from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from .models import Drone, DeliveryRequest, Route, Location, DroneTelemetry, DeliveryMetrics

@admin.register(Location)
class LocationAdmin(OSMGeoAdmin):
    list_display = ('name', 'is_depot', 'address')
    list_filter = ('is_depot',)
    search_fields = ('name', 'address')

@admin.register(Drone)
class DroneAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'battery_level', 'max_payload', 'last_maintenance')
    list_filter = ('status',)
    search_fields = ('name',)

@admin.register(DeliveryRequest)
class DeliveryRequestAdmin(OSMGeoAdmin):
    list_display = ('id', 'status', 'pickup_location', 'dropoff_location', 'weight', 'assigned_drone')
    list_filter = ('status', 'priority')
    search_fields = ('pickup_location__name', 'dropoff_location__name')
    readonly_fields = ('created_at', 'distance', 'estimated_duration', 'actual_duration')

@admin.register(Route)
class RouteAdmin(OSMGeoAdmin):
    list_display = ('id', 'delivery', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(DroneTelemetry)
class DroneTelemetryAdmin(OSMGeoAdmin):
    list_display = ('drone', 'timestamp', 'battery_level', 'speed', 'altitude')
    list_filter = ('drone',)
    readonly_fields = ('timestamp',)

@admin.register(DeliveryMetrics)
class DeliveryMetricsAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_deliveries', 'successful_deliveries', 'success_rate', 'average_delivery_time', 'average_cost_per_km')
    readonly_fields = ('success_rate',)
    
    def success_rate(self, obj):
        return f"{obj.success_rate()}%"
    success_rate.short_description = 'Success Rate'