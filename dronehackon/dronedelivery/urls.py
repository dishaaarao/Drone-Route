from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from dronedelivery import views
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register(r'drones', views.DroneViewSet)
router.register(r'deliveries', views.DeliveryRequestViewSet)
router.register(r'routes', views.RouteViewSet)
router.register(r'locations', views.LocationViewSet)
router.register(r'telemetry', views.DroneTelemetryViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)