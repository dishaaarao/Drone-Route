from celery import shared_task
from django.utils import timezone
from .models import Drone, DeliveryRequest, DroneTelemetry, DeliveryMetrics
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import random
import math
from django.contrib.gis.geos import Point

@shared_task
def simulate_drone_movement():
    # Get all active drones
    active_drones = Drone.objects.filter(status='in_transit')
    
    for drone in active_drones:
        # Get active delivery
        delivery = DeliveryRequest.objects.filter(
            assigned_drone=drone,
            status__in=['assigned', 'in_progress']
        ).first()
        
        if not delivery:
            continue
        
        # Update delivery status to in_progress if needed
        if delivery.status == 'assigned':
            delivery.status = 'in_progress'
            delivery.save(update_fields=['status'])
        
        # Simulate movement
        current_location = drone.current_location or delivery.pickup_location.coordinates
        target_location = delivery.dropoff_location.coordinates
        
        # Calculate distance to target
        dx = target_location.x - current_location.x
        dy = target_location.y - current_location.y
        distance = math.sqrt(dx**2 + dy**2)
        
        # If we're close enough, mark as delivered
        if distance < 0.0001:  # ~11 meters
            delivery.status = 'delivered'
            delivery.actual_duration = (timezone.now() - delivery.created_at).total_seconds() / 60
            delivery.save()
            
            # Update drone status
            drone.status = 'idle'
            drone.save()
            
            # Update metrics
            update_delivery_metrics(delivery)
            
            # Send notification
            send_delivery_update(delivery.id, 'delivered')
            continue
        
        # Move towards target (simplified)
        speed = 0.0001  # degrees per update
        step_x = (dx / distance) * speed
        step_y = (dy / distance) * speed
        
        new_x = current_location.x + step_x
        new_y = current_location.y + step_y
        
        # Update drone location
        drone.current_location = Point(new_x, new_y, srid=4326)
        drone.battery_level = max(0, drone.battery_level - 0.1)  # Consume battery
        
        # If battery is low, return to nearest depot
        if drone.battery_level < 20 and delivery.status != 'returning':
            delivery.status = 'returning'
            delivery.save(update_fields=['status'])
            send_delivery_update(delivery.id, 'returning_to_charge')
        elif drone.battery_level < 1:
            # Emergency landing
            drone.status = 'maintenance'
            delivery.status = 'failed'
            delivery.save(update_fields=['status'])
            send_delivery_update(delivery.id, 'emergency_landing')
        
        drone.save()
        
        # Record telemetry
        telemetry = DroneTelemetry.objects.create(
            drone=drone,
            location=drone.current_location,
            battery_level=drone.battery_level,
            speed=random.uniform(5, 15),  # m/s
            altitude=random.uniform(50, 150)  # meters
        )
        
        # Send real-time update
        send_telemetry_update(drone.id, telemetry)

def send_telemetry_update(drone_id, telemetry):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"drone_{drone_id}",
        {
            'type': 'telemetry_update',
            'message': {
                'location': {
                    'type': 'Point',
                    'coordinates': [telemetry.location.x, telemetry.location.y]
                },
                'battery_level': telemetry.battery_level,
                'speed': telemetry.speed,
                'altitude': telemetry.altitude,
                'timestamp': telemetry.timestamp.isoformat()
            }
        }
    )

def send_delivery_update(delivery_id, status):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"delivery_{delivery_id}",
        {
            'type': 'delivery_update',
            'message': {
                'status': status,
                'timestamp': timezone.now().isoformat()
            }
        }
    )

def update_delivery_metrics(delivery):
    # Get or create metrics for today
    today = timezone.now().date()
    metrics, created = DeliveryMetrics.objects.get_or_create(
        date=today,
        defaults={
            'total_deliveries': 0,
            'successful_deliveries': 0,
            'average_delivery_time': 0,
            'average_cost_per_km': 0,
            'total_distance': 0
        }
    )
    
    # Update metrics
    metrics.total_deliveries += 1
    if delivery.status == 'delivered':
        metrics.successful_deliveries += 1
    
    # Calculate average delivery time
    total_deliveries = DeliveryRequest.objects.filter(
        created_at__date=today,
        status='delivered'
    ).count()
    
    total_delivery_time = sum(
        (d.actual_duration or 0) 
        for d in DeliveryRequest.objects.filter(
            created_at__date=today,
            status='delivered'
        )
    )
    
    if total_deliveries > 0:
        metrics.average_delivery_time = total_delivery_time / total_deliveries
    
    # Calculate average cost per km (simplified)
    total_distance = sum(
        (d.distance or 0) / 1000  # Convert to km
        for d in DeliveryRequest.objects.filter(created_at__date=today)
    )
    
    metrics.total_distance = total_distance
    
    # Simplified cost calculation
    if total_distance > 0:
        metrics.average_cost_per_km = (total_deliveries * 10) / total_distance  # $10 per delivery
    
    metrics.save()