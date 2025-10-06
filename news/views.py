from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.gis.geos import LineString
from .models import Drone, DeliveryRequest, Route, Location, DroneTelemetry
from .serializers import (
    DroneSerializer, 
    DeliveryRequestSerializer, 
    RouteSerializer,
    LocationSerializer,
    DroneTelemetrySerializer
)
from django.utils import timezone
import random
from django.db.models import Q
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class DroneViewSet(viewsets.ModelViewSet):
    queryset = Drone.objects.all()
    serializer_class = DroneSerializer
    
    @action(detail=True, methods=['post'])
    def update_telemetry(self, request, pk=None):
        drone = self.get_object()
        serializer = DroneTelemetrySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(drone=drone)
            
            # Send real-time update
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"drone_{drone.id}",
                {
                    'type': 'telemetry_update',
                    'message': serializer.data
                }
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeliveryRequestViewSet(viewsets.ModelViewSet):
    queryset = DeliveryRequest.objects.all()
    serializer_class = DeliveryRequestSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Calculate route and assign drone
            delivery = serializer.save()
            self.assign_drone_and_route(delivery)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def assign_drone_and_route(self, delivery):
        # Find available drones near pickup location
        available_drones = Drone.objects.filter(
            status='idle',
            current_location__distance_lte=(delivery.pickup_location.coordinates, D(km=10))
        ).annotate(
            distance=Distance('current_location', delivery.pickup_location.coordinates)
        ).order_by('distance')
        
        if available_drones.exists():
            drone = available_drones.first()
            delivery.assigned_drone = drone
            delivery.status = 'assigned'
            delivery.save()
            
            # Create initial route
            self.calculate_route(delivery, drone)
            
            # Update drone status
            drone.status = 'in_transit'
            drone.save()
            
            return True
        return False
    
    def calculate_route(self, delivery, drone):
        # This is a simplified version - you would integrate with a routing service like OSRM
        # or implement A* algorithm here
        pickup = delivery.pickup_location.coordinates
        dropoff = delivery.dropoff_location.coordinates
        
        # For demo, create a simple straight line path
        path = LineString([pickup, dropoff], srid=4326)
        
        # Create route
        route = Route.objects.create(
            delivery=delivery,
            path=path
        )
        
        # Calculate distance (in meters)
        delivery.distance = path.length
        delivery.estimated_duration = (path.length / 1000) / 15 * 60  # Assuming 15 m/s speed
        delivery.save()
        
        return route

class RouteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer

class DroneTelemetryViewSet(viewsets.ModelViewSet):
    queryset = DroneTelemetry.objects.all()
    serializer_class = DroneTelemetrySerializer