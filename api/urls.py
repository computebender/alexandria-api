from django.urls import include, path
from .views import HelloWorldViewSet, JournalEntryViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'journal-entries', JournalEntryViewSet)
router.register(r'hello-world', HelloWorldViewSet, basename='hello-world')

urlpatterns = [
    path('', include(router.urls)),
]

