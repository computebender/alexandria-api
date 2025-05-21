from celery import shared_task
from time import sleep

@shared_task
def add_task(x, y):
    print("Starting background task")
    sleep(5)
    print("Task completed")
    return x + y