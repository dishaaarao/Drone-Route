from django.urls import re_path
from dronedelivery import consumers

websocket_urlpatterns = [
    re_path(r'ws/drone/(?P<drone_id>\w+)/$', consumers.DroneConsumer.as_asgi()),
    re_path(r'ws/delivery/(?P<delivery_id>\w+)/$', consumers.DeliveryConsumer.as_asgi()),
]