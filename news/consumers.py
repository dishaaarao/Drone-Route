import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Drone, DeliveryRequest

class DroneConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.drone_id = self.scope['url_route']['kwargs']['drone_id']
        self.drone_group_name = f'drone_{self.drone_id}'

        # Join drone group
        await self.channel_layer.group_add(
            self.drone_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave drone group
        await self.channel_layer.group_discard(
            self.drone_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to room group
        await self.channel_layer.group_send(
            self.drone_group_name,
            {
                'type': 'telemetry_update',
                'message': message
            }
        )

    # Receive message from room group
    async def telemetry_update(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))

class DeliveryConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.delivery_id = self.scope['url_route']['kwargs']['delivery_id']
        self.delivery_group_name = f'delivery_{self.delivery_id}'

        # Join delivery group
        await self.channel_layer.group_add(
            self.delivery_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave delivery group
        await self.channel_layer.group_discard(
            self.delivery_group_name,
            self.channel_name
        )

    # Receive message from room group
    async def delivery_update(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))