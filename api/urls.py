from django.urls import include, path
from .views import HelloWorldViewSet, JournalEntryViewSet, add_background, streaming_test
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'journal-entries', JournalEntryViewSet)
router.register(r'hello-world', HelloWorldViewSet, basename='hello-world')

urlpatterns = [
    path('add-background/', add_background, name='add_background'),
    path('streaming-test/<str:task_id>/', streaming_test, name='streaming-test'),
    path('', include(router.urls)),
]

