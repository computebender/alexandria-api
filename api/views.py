import datetime
import json
import time
import asyncio
import uuid

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

        channel_name = f'sse_{task_id}_{uuid.uuid4()}_{request.META.get("REMOTE_ADDR", "")}_{request.META.get("REMOTE_PORT", "")}'
        
        await channel_layer.group_add(task_group_name, channel_name)

        try:
            initial_message = {'type': 'connected', 'task_id': task_id}
            try:
                yield f"data: {json.dumps(initial_message)}\n\n"
            except Exception as e_yield_initial:
                # If initial send fails, client might already be gone.
                # No point in continuing. Finally block will handle cleanup.
                return
           
            while True:
                try:
                    # Check for messages with a timeout
                    message = await asyncio.wait_for(
                        channel_layer.receive(channel_name),
                        timeout=10.0
                    )
                    
                    if message:
                        try:
                            yield f"data: {json.dumps(message)}\n\n"
                        except Exception as e_yield_message:
                            # Client likely disconnected
                            # Exit the loop to allow cleanup
                            break 

                        if message.get('type') in ['task_complete', 'task_error']:
                            break
                
                except asyncio.TimeoutError:
                    # No message received within the timeout, send a heartbeat
                    try:
                        yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                    except Exception as e_yield_heartbeat:
                        # Client likely disconnected
                        # Exit the loop to allow cleanup
                        break 
                
                except asyncio.CancelledError:
                    # The task was cancelled. Re-raise to ensure proper cleanup by the ASGI server.
                    raise 

                except Exception as e:
                    # Handle other unexpected errors
                    error_payload = {'type': 'stream_error', 'detail': str(e)}
                    try:
                        yield f"data: {json.dumps(error_payload)}\n\n"
                    except Exception:
                        # Failed to send error to client, likely disconnected
                        pass
                    break # Exit loop on other errors
        
        finally:
            # Clean up: remove from group
            await channel_layer.group_discard(task_group_name, channel_name)

     
    response = StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream'
        )
    response['Cache-Control'] = 'no-cache'
    return response
