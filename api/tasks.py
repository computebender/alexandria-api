from celery import shared_task
import time

@shared_task(bind=True)
def add_task(self):
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    
    channel_layer = get_channel_layer()
    task_group_name = f'task_{self.request.id}'
    
    def send_update(message_type, **kwargs):
        message = {
            'type': message_type,
            'task_id': self.request.id,
            **kwargs
        }
        async_to_sync(channel_layer.group_send)(task_group_name, message)
    
    try:

        send_update('task_started', 
                   progress=0, 
                   message='Starting API data fetch...')
        
        total_steps = 10

        for step in range(total_steps):
            time.sleep(3)

            progress_percentage = int((step + 1) / total_steps * 100)

            send_update('progress_update',
                       progress=progress_percentage,
                       message=f'Completed step {step + 1} of {total_steps}')

        time.sleep(2)
        result_data = {
            'completion_time': time.time()
        }
        
        send_update('task_complete', result=result_data)

        return result_data
    
    except Exception as e:
        send_update('task_error', error=str(e))
        raise