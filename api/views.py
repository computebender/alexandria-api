import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import OrderingFilter
from rest_framework.decorators import action

from .tasks import add_task
from .pagination import RelativeUrlPagination
from .serealizers import JournalEntrySerializer
from .models import JournalEntry



class HelloWorldViewSet(viewsets.ViewSet):
    def list(self, request):
        return Response({"message": "Hello, world!"}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='add-background')
    def add_background(self, request):
        datetime_string = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        data = {
            'message': f'Running at {datetime_string}!'
        }

        add_task.delay(1, 2)

        return Response(data, status=status.HTTP_200_OK)

    
class JournalEntryViewSet(viewsets.ModelViewSet):
    queryset = JournalEntry.objects.all()
    serializer_class = JournalEntrySerializer
    pagination_class = RelativeUrlPagination

    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']