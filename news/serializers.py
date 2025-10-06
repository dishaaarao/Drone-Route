from rest_framework import serializers
from .models import Drone, DeliveryRequest, Route, Location, DroneTelemetry

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name', 'coordinates', 'is_depot', 'address']
        read_only_fields = ['id']

class DroneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Drone
        fields = ['id', 'name', 'status', 'battery_level', 'max_payload', 
                 'current_location', 'last_maintenance']
        read_only_fields = ['id', 'status', 'battery_level', 'current_location']

class DeliveryRequestSerializer(serializers.ModelSerializer):
    pickup_location = LocationSerializer()
    dropoff_location = LocationSerializer()
    
    class Meta:
        model = DeliveryRequest
        fields = ['id', 'pickup_location', 'dropoff_location', 'weight', 'status',
                 'created_at', 'assigned_drone', 'distance', 'estimated_duration',
                 'actual_duration', 'priority']
        read_only_fields = ['id', 'status', 'created_at', 'distance', 
                           'estimated_duration', 'actual_duration']
    
    def create(self, validated_data):
        pickup_data = validated_data.pop('pickup_location')
        dropoff_data = validated_data.pop('dropoff_location')
        
        # Get or create locations
        pickup_location, _ = Location.objects.get_or_create(
            name=pickup_data['name'],
            defaults={
                'coordinates': pickup_data['coordinates'],
                'address': pickup_data.get('address', '')
            }
        )
        
        dropoff_location, _ = Location.objects.get_or_create(
            name=dropoff_data['name'],
            defaults={
                'coordinates': dropoff_data['coordinates'],
                'address': dropoff_data.get('address', '')
            }
        )
        
        # Create delivery request
        delivery = DeliveryRequest.objects.create(
            pickup_location=pickup_location,
            dropoff_location=dropoff_location,
            **validated_data
        )
        
        return delivery

class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ['id', 'delivery', 'path', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class DroneTelemetrySerializer(serializers.ModelSerializer):
    class Meta:
        model = DroneTelemetry
        fields = ['id', 'drone', 'timestamp', 'location', 'battery_level', 
                 'speed', 'altitude']
        read_only_fields = ['id', 'timestamp']