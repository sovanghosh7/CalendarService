from django.conf.urls import url, include
from rest_framework import routers
from .views import EventViewSet, UserViewSet, CalenderApiRootView

router = routers.DefaultRouter()
router.APIRootView = CalenderApiRootView

router.register(r'event', EventViewSet)
router.register(r'user', UserViewSet)

urlpatterns = [
    url('', include(router.urls)),
]
