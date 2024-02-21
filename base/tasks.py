from celery import shared_task
from base.models import *
from base.task_helpers import *
from base.send_message_vonage import *
import json
from django.db import IntegrityError, transaction
from django.core.cache import cache
logger = logging.getLogger(__name__)


@shared_task
def get_messages():
    count = cache.get('get_messages_count', 0)
    phone_numbers = PhoneNumber.objects.filter(study_completed=False, opted_in=True, active=True)
    logger.info(f"Found {phone_numbers.count()} phone numbers active in the study")
    for phone_number in phone_numbers:
        week_num, current_weekday = get_week_num_and_current_weekday(phone_number.created_at,count)
        logger.info(f"Phone number {phone_number.id} belongs to arm {phone_number.arm.name} and is in week {week_num} and day {current_weekday}")

        if week_num == 0 or current_weekday > 5:
            logger.info(f'Skipping {phone_number.id} because it is in week {week_num} and day{current_weekday}')
            continue

        # Ensuring atomic transactions to avoid partial updates
        with transaction.atomic():
            try:
                if current_weekday == 1 and week_num <= settings.TOTAL_TOPICS:
                    # Handling for both control and ai_chat arms with unified logging and error handling
                    handle_topic_selection(phone_number, week_num, current_weekday)

                if current_weekday == 2 and week_num <= settings.TOTAL_TOPICS and 'ai_chat' in phone_number.arm.name.lower():
                    # Example for handling goals
                    handle_goals(phone_number, week_num, current_weekday)

                if current_weekday == 5 and week_num <= settings.TOTAL_TOPICS and 'ai_chat' in phone_number.arm.name.lower():
                    # Example for handling feedback on goals
                    handle_goals_feedback(phone_number, week_num, current_weekday)

                if week_num == (settings.TOTAL_TOPICS + 1) and current_weekday == 1:
                    # Handling for sending final pilot message
                    handle_final_pilot_message(phone_number, week_num, current_weekday)

                # Handling scheduled info messages
                if week_num <= settings.TOTAL_TOPICS:
                    handle_scheduled_info_messages(phone_number, week_num, current_weekday)
                
            except Exception as e:
                logger.error(f"Error processing phone number {phone_number.id}: {e}")

    count += 1
    cache.set('get_messages_count', count)
    return None

def handle_topic_selection(phone_number, week_num, current_weekday):
    # Check if the message for topic selection needs to be sent
    message_tracker, _ = MessageTracker.objects.get_or_create(
        phone_number=phone_number, 
        week_no=week_num, 
        defaults={'sent_topic_selection_message': False}
    )
    
    # Only proceed if the topic selection message has not been sent
    if not message_tracker.sent_topic_selection_message:
        if 'control' in phone_number.arm.name.lower():
                logger.info(f"Assigning topic number {week_num} to {phone_number.id}")
                try:
                    weekly_topic, created = WeeklyTopic.objects.get_or_create(phone_number=phone_number, topic_id=week_num, week_number=week_num)
                    logger.info(f"WeeklyTopic object {weekly_topic.id} {'created' if created else 'already existed'}")
                except IntegrityError:
                    logger.error(f"IntegrityError when trying to create WeeklyTopic object for {phone_number.id}")
        else:
            message, default_topic_id, picklist_json = get_topic_selection_message(phone_number, week_num)
            if message:
                SendMessage.objects.create(
                    phone_number=phone_number, message=message, route='outgoing_scheduled_topic_selection',
                    week_num=week_num,picklist=picklist_json,current_weekday=current_weekday,
                    default_topic_id=default_topic_id, message_tracker_col='sent_topic_selection_message')
                # Mark as sent
                message_tracker.sent_topic_selection_message = True
                message_tracker.save()
                logger.info(f"Topic selection message sent to {phone_number.id} for week {week_num}")

def handle_goals(phone_number, week_num, current_weekday):
    message_tracker, _ = MessageTracker.objects.get_or_create(
        phone_number=phone_number, 
        week_no=week_num, 
        defaults={'sent_goal_message': False}
    )
    
    if not message_tracker.sent_goal_message:
        message, picklist_json = get_goals_message(phone_number, week_num)
        if message:
            SendMessage.objects.create(
                phone_number=phone_number, message=message, route='outgoing_scheduled_goal',
                week_num=week_num,picklist=picklist_json,current_weekday=current_weekday)
            message_tracker.sent_goal_message = True
            message_tracker.save()
            logger.info(f"Goals message sent to {phone_number.id} for week {week_num}")

def handle_goals_feedback(phone_number, week_num, current_weekday):
    message_tracker, _ = MessageTracker.objects.get_or_create(
        phone_number=phone_number, 
        week_no=week_num, 
        defaults={'sent_goal_feedback_message': False}
    )
    
    if not message_tracker.sent_goal_feedback_message:
        message, picklist_json = get_feedback_message(phone_number, week_num)
        if message:
            SendMessage.objects.create(
                phone_number=phone_number, message=message, route='outgoing_goal_feedback',
                week_num=week_num,picklist=picklist_json,current_weekday=current_weekday)
            message_tracker.sent_goal_feedback_message = True
            message_tracker.save()
            logger.info(f"Goals feedback message sent to {phone_number.id} for week {week_num}")

def handle_final_pilot_message(phone_number, week_num, current_weekday):
    if not phone_number.final_pilot_message_sent:
        message, include_name = get_final_message(phone_number)
        if message:
            SendMessage.objects.create(phone_number=phone_number, message=message, 
                route='outgoing_final_pilot_message',week_num=week_num,picklist=None,
                current_weekday=current_weekday,include_name=include_name)
            phone_number.final_pilot_message_sent = True
            phone_number.save()
            logger.info(f"Final pilot message sent to {phone_number.id}")

def handle_scheduled_info_messages(phone_number, week_num, current_weekday):
    message_tracker_col = f'sent_info_message_{current_weekday}'
    if not getattr(MessageTracker.objects.filter(phone_number=phone_number, week_no=week_num).first(), message_tracker_col, False):
        message, include_name, picklist_json, message_tracker_col_updated = send_scheduled_message(phone_number, week_num, current_weekday)
        logger.info(f"message for {phone_number.id} is {message}")
        if message:
            SendMessage.objects.create(
                phone_number=phone_number, message=message, route='outgoing_scheduled_info',
                week_num=week_num, picklist=picklist_json,current_weekday=current_weekday,
                include_name=include_name)
            # Update the message_tracker to mark the message as sent
            MessageTracker.objects.filter(phone_number=phone_number, week_no=week_num).update(**{message_tracker_col: True})
            logger.info(f"Scheduled info message sent to {phone_number.id} for week {week_num}, day {current_weekday}")
        
                    
@shared_task
def send_messages():
    scheduled_messages = SendMessage.objects.filter(sent=False,route__in=['outgoing_scheduled_info','outgoing_scheduled_goal','outgoing_goal_feedback'])
    for message in scheduled_messages:
        success = retry_send_message_vonage(message.message, message.phone_number, message.route, max_retries=3, retry_delay=5)
        if success:
            message.sent = True
            message.save()
            TextMessage.objects.create(phone_number=message.phone_number, message=message.message, route=message.route)
            MessageTracker.objects.update_or_create(phone_number=message.phone_number,week_no = message.week_num,defaults={message.message_tracker_col: True})
            if message.picklist:
                Picklist.objects.create(phone_number=message.phone_number, context=message.route, picklist=message.picklist)
            
@shared_task
def send_topic_selection_message():
    scheduled_messages = SendMessage.objects.filter(sent=False,route='outgoing_scheduled_topic_selection')
    for message in scheduled_messages:
        success = retry_send_message_vonage(message.message, message.phone_number, message.route, max_retries=3, retry_delay=5,include_name=message.include_name)
        if success:
            message.sent = True
            message.save()
            TextMessage.objects.create(phone_number=message.phone_number, message=message.message, route=message.route)
            MessageTracker.objects.update_or_create(phone_number=message.phone_number,week_no = message.week_num,defaults={message.message_tracker_col: True})
            if message.picklist:
                Picklist.objects.create(phone_number=message.phone_number, context=message.route, picklist=message.picklist)

                

@shared_task
def send_final_pilot_message():
    scheduled_messages = SendMessage.objects.filter(sent=False,route='outgoing_final_pilot_message')
    for message in scheduled_messages:
        success = retry_send_message_vonage(message.message, message.phone_number, message.route, max_retries=3, retry_delay=5,include_name=message.include_name)
        if success:
            message.sent = True
            message.save()
            TextMessage.objects.create(phone_number=message.phone_number, message=message.message, route=message.route)
            PhoneNumber.objects.filter(id=message.phone_number.id).update(final_pilot_message_sent=True,study_completed=True)

from django.db import connection
@shared_task
def update_phone_number_created_at():
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE base_phonenumber
            SET created_at = created_at - INTERVAL '1 day'
        """)
