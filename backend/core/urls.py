from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuthViewSet, UserProfileViewSet, JobViewSet, ApplicationTrackerViewSet

router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'profile', UserProfileViewSet, basename='profile')
router.register(r'jobs', JobViewSet, basename='job')
router.register(r'applications', ApplicationTrackerViewSet, basename='application')

urlpatterns = [
    path('', include(router.urls)),
]
