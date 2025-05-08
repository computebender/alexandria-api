from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination


from .serealizers import JournalEntrySerializer
from .models import JournalEntry

class HelloWorldViewSet(viewsets.ViewSet):
    def list(self, request):
        return Response({"message": "Hello, world!"}, status=status.HTTP_200_OK)
    
class JournalEntryViewSet(viewsets.ModelViewSet):
    queryset = JournalEntry.objects.all()
    serializer_class = JournalEntrySerializer