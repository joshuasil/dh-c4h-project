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

# app.conf.beat_schedule = {
#     'trigger_task_chain_every_60_seconds': {
#         'task': 'base.tasks.send_messages_chain',  # Use the correct path to your task
#         'schedule': 70.0,  # Run every 60 seconds
#     },
# }

app.conf.beat_schedule = {
    'getting messages': {
        'task': 'base.tasks.get_messages',
        # Runs first after 'update futuredate testing', starting the cycle
        'schedule': crontab(hour=6, minute=0),
    },
    'sending topic selection': {
        'task': 'base.tasks.send_topic_selection_message',
        # Runs immediately after 'getting messages', before other tasks
        'schedule': crontab(day_of_week=1, hour=9, minute=0),
    },
    'sending general messages': {
        'task': 'base.tasks.send_messages',
        # Ensures it runs after 'sending topic selection'
        'schedule': crontab(hour=10, minute=0),
    },
    'sending final message': {
        'task': 'base.tasks.send_final_pilot_message',
        # Scheduled after 'sending general messages'
        'schedule': crontab(hour=10, minute=15),
    },
    'sending final study survey': {
        'task': 'base.tasks.send_final_study_survey',
        # Scheduled last among these tasks, after 'sending final message'
        'schedule': crontab(hour=10, minute=16),
    },
}





# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

