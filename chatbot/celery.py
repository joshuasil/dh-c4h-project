# celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab
from celery import chain


# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatbot.settings')

# Create a Celery instance and configure it using the settings from Django.
app = Celery('chatbot')

# Load task modules from all registered Django app configs.
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    'getting messages': {
        'task': 'base.tasks.get_messages',
        'schedule': 150,
    },
    'sending topic selection': {
        'task': 'base.tasks.send_topic_selection_message',
        'schedule': 160,
    },
    'sending general messages': {
        'task': 'base.tasks.send_messages',
        'schedule': 170,
    },
    'sending final message': {
        'task': 'base.tasks.send_final_pilot_message',
        'schedule': 175,
    },
    # 'updating number time for testing': {
    #     'task': 'base.tasks.update_phone_number_created_at',
    #     'schedule': 70,
    # },
    
}



# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

