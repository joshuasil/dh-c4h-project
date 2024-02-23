# celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab
from celery import chain
# from base.tasks import update_futuredate_testing, get_messages, send_topic_selection_message, send_messages, send_final_pilot_message, send_final_study_survey


# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatbot.settings')

# Create a Celery instance and configure it using the settings from Django.
app = Celery('chatbot')

# Load task modules from all registered Django app configs.
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    # Schedule the wrapper task to run every 60 seconds
    'trigger_task_chain_every_60_seconds': {
        'task': 'base.tasks.send_messages_chain',  # Use the correct path to your task
        'schedule': 70.0,  # Run every 60 seconds
    },
}

# app.conf.beat_schedule = {
#     'update futuredate testing': {
#         'task': 'base.tasks.update_futuredate_testing',
#         # Initiates a new cycle every 20 minutes
#         'schedule': crontab(minute='*/20'),
#     },
#     'getting messages': {
#         'task': 'base.tasks.get_messages',
#         # Runs first after 'update futuredate testing', starting the cycle
#         'schedule': crontab(minute='1-19/20'),
#     },
#     'sending topic selection': {
#         'task': 'base.tasks.send_topic_selection_message',
#         # Runs immediately after 'getting messages', before other tasks
#         'schedule': crontab(minute='2-19/20'),
#     },
#     'sending general messages': {
#         'task': 'base.tasks.send_messages',
#         # Ensures it runs after 'sending topic selection'
#         'schedule': crontab(minute='3-19/20'),
#     },
#     'sending final message': {
#         'task': 'base.tasks.send_final_pilot_message',
#         # Scheduled after 'sending general messages'
#         'schedule': crontab(minute='4-19/20'),
#     },
#     'sending final study survey': {
#         'task': 'base.tasks.send_final_study_survey',
#         # Scheduled last among these tasks, after 'sending final message'
#         'schedule': crontab(minute='5-19/20'),
#     },
# }





# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

