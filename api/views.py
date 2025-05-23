import datetime
import json
import time
import asyncio

from django.http import StreamingHttpResponse

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import OrderingFilter
from rest_framework.decorators import api_view
from rest_framework.renderers import JSONRenderer


from channels.layers import get_channel_layer

from .tasks import add_task
from .pagination import RelativeUrlPagination
from .serealizers import JournalEntrySerializer
from .models import JournalEntry

@api_view(['POST'])
def add_background(self):
    task = add_task.delay()

    return Response({
        'task_id': task.id,
        'sse_url': f'/api/streaming-test/{task.id}/',
    })


class HelloWorldViewSet(viewsets.ViewSet):
    def list(self, request):
        return Response({"message": "Hello, world!"}, status=status.HTTP_200_OK)


    
class JournalEntryViewSet(viewsets.ModelViewSet):
    queryset = JournalEntry.objects.all()
    serializer_class = JournalEntrySerializer
    pagination_class = RelativeUrlPagination

    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


async def streaming_test(request, task_id):
    async def event_stream():
        channel_layer = get_channel_layer()
        task_group_name = f'task_{task_id}'

        channel_name = f'sse_{task_id}_{int(time.time() * 1000)}'
        
        await channel_layer.group_add(task_group_name, channel_name)

        try:
            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connected', 'task_id': task_id})}\n\n"

            while True:
                try:
                    # Check for messages with a timeout
                    message = await channel_layer.receive(channel_name)
                    
                    if message:
                        # Forward the message to the client
                        yield f"data: {json.dumps(message)}\n\n"
                        
                        # If task is complete or errored, break the loop
                        if message.get('type') in ['task_complete', 'task_error']:
                            break
                except:
                    # If no message received, send a heartbeat
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                    await asyncio.sleep(1)
        
        finally:
            # Clean up: remove from group
            await channel_layer.group_discard(task_group_name, channel_name)

     
    response = StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream'
        )
    response['Cache-Control'] = 'no-cache'
    response['Connection'] = 'keep-alive'
    return response
