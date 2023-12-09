import logging
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import register_events, register_job
from .scheduled_content import *
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.base import JobLookupError
from django.conf import settings


logger = logging.getLogger(__name__)

def start():
    if settings.DEBUG:
        try:
            scheduler = BackgroundScheduler(settings.SCHEDULER_CONFIG, job_defaults={'max_instances': 1, 'misfire_grace_time': 150})
            jobs = [
                (send_topic_selection_message, 'Send Topic Selection Message',CronTrigger(hour=19, minute=10)),

                (send_scheduled_message, 'Send Scheduled Info Message',CronTrigger(hour=19, minute=11)),
                (send_goal_message, 'Send Goals Message',CronTrigger(hour=19, minute=12)),
                (send_goal_feedback, 'Send Goals Feedback Message',CronTrigger(hour=19, minute=13)),
                (send_final_pilot_message, 'Send Final Pilot Message',CronTrigger(hour=19, minute=14))
            ]
            for job in jobs:
                scheduler.add_job(job[0], id=job[1], replace_existing=True, trigger=job[2], coalesce=True)
            register_events(scheduler)
            scheduler.start()
            logger.info('Scheduler started successfully')
        except Exception as e:
            logger.error(f'Error starting scheduler: {e}')
    else:
        logger.info('Scheduler not started because DEBUG is False')