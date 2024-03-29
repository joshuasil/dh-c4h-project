from celery import shared_task
from base.models import *
from base.task_helpers import *
from base.send_message_vonage import *
import json
from django.db import IntegrityError, transaction
from django.core.cache import cache
logger = logging.getLogger(__name__)
from celery import current_app

@shared_task
def get_messages():
    phone_numbers = PhoneNumber.objects.filter(study_completed=False, opted_in=True, active=True)
    logger.info(f"Found {phone_numbers.count()} phone numbers active in the study")
    for phone_number in phone_numbers:
        week_num, current_weekday = get_week_num_and_current_weekday(phone_number.created_at)
        logger.info(f"Phone number {phone_number.id} belongs to arm {phone_number.arm.name} and is in week {week_num} and day {current_weekday}")

        if week_num == 0 or current_weekday > 5:
            logger.info(f'Skipping {phone_number.id} because it is in week {week_num} and day{current_weekday}')
            continue

        # Ensuring atomic transactions to avoid partial updates
        with transaction.atomic():
            try:
                if current_weekday == 1 and week_num <= settings.TOTAL_TOPICS:
                    logger.info(f"Handling topic selection for {phone_number.id}")
                    handle_topic_selection(phone_number, week_num, current_weekday)

                if current_weekday == 2 and week_num <= settings.TOTAL_TOPICS and 'ai_chat' in phone_number.arm.name.lower():
                    logger.info(f"Handling goals for {phone_number.id}")
                    handle_goals(phone_number, week_num, current_weekday)

                if current_weekday == 5 and week_num <= settings.TOTAL_TOPICS and 'ai_chat' in phone_number.arm.name.lower():
                    logger.info(f"Handling goals feedback for {phone_number.id}")
                    handle_goals_feedback(phone_number, week_num, current_weekday)

                if week_num == 10 and current_weekday == 1:
                    logger.info(f"Handling final pilot message for {phone_number.id}")
                    handle_final_pilot_message(phone_number, week_num, current_weekday)

                # Handling scheduled info messages
                if week_num <= settings.TOTAL_TOPICS:
                    logger.info(f"Handling scheduled info messages for {phone_number.id} with language {phone_number.language} and week {week_num} and day {current_weekday}")
                    handle_scheduled_info_messages(phone_number, week_num, current_weekday)
                
            except Exception as e:
                logger.error(f"Error processing phone number {phone_number.id}: {e}")

    #time.sleep(10)

def handle_topic_selection(phone_number, week_num, current_weekday):
    message_tracker, created = MessageTracker.objects.get_or_create(phone_number=phone_number, 
                            week_no=week_num, defaults={'sent_topic_selection_message': False})
    if created:
        logger.warning(f"Message tracker created for {phone_number.id} and week {week_num}")
    try:
        send_message_obj = SendMessage.objects.get(phone_number=phone_number, week_num=week_num, route='outgoing_scheduled_topic_selection')
        logger.info(f"Skipping because SendMessage object found for phone number {phone_number.id} and week {week_num}")
    except SendMessage.DoesNotExist:
        send_message_obj = None
    # Only proceed if the topic selection message has not been sent
    if not send_message_obj:
        if 'control' in phone_number.arm.name.lower():
                logger.info(f"Assigning topic number {week_num} to {phone_number.id}")
                try:
                    weekly_topic, created = WeeklyTopic.objects.get_or_create(phone_number=phone_number, topic_id=week_num, week_number=week_num)
                    logger.info(f"WeeklyTopic object {weekly_topic.id} {'created' if created else 'already existed'}")
                except IntegrityError:
                    logger.error(f"IntegrityError when trying to create WeeklyTopic object for {phone_number.id}")
        else:
            message, default_topic_id, picklist_json = get_topic_selection_message(phone_number, week_num)
            logger.info(f"message for {phone_number.id} and {phone_number.language} is {message}")
            if message:
                SendMessage.objects.create(
                    phone_number=phone_number, message=message, route='outgoing_scheduled_topic_selection',
                    week_num=week_num,picklist=picklist_json,current_weekday=current_weekday,
                    default_topic_id=default_topic_id, message_tracker_col='sent_topic_selection_message')
                # Mark as sent
                # message_tracker.sent_topic_selection_message = True
                # message_tracker.save()
                logger.info(f"Topic selection message sent to {phone_number.id} for week {week_num}")

def handle_goals(phone_number, week_num, current_weekday):
    message_tracker, created = MessageTracker.objects.get_or_create(
        phone_number=phone_number, 
        week_no=week_num, 
        defaults={'sent_goal_message': False}
    )
    if created:
        logger.warning(f"message tracker created for {phone_number.id} and week {week_num}")
    try:
        send_message_obj = SendMessage.objects.get(phone_number=phone_number, week_num=week_num, route='outgoing_scheduled_goal')
        logger.info(f"Skipping because SendMessage object found for phone number {phone_number.id} and week {week_num}")
    except SendMessage.DoesNotExist:
        send_message_obj = None
    if not send_message_obj:
        message, picklist_json = get_goals_message(phone_number, week_num)
        logger.info(f"message for {phone_number.id} with language {phone_number.language} is {message}")
        if message:
            SendMessage.objects.create(
                phone_number=phone_number, message=message, route='outgoing_scheduled_goal',
                week_num=week_num,picklist=picklist_json,current_weekday=current_weekday,message_tracker_col='sent_goal_message')
            # message_tracker.sent_goal_message = True
            # message_tracker.save()
            logger.info(f"Goals message sent to {phone_number.id} for week {week_num}")

def handle_goals_feedback(phone_number, week_num, current_weekday):
    message_tracker, created = MessageTracker.objects.get_or_create(
        phone_number=phone_number, 
        week_no=week_num, 
        defaults={'sent_goal_feedback_message': False}
    )
    if created:
        logger.warning(f"message tracker created for {phone_number.id} and week {week_num}")

    try:
        send_message_obj = SendMessage.objects.get(phone_number=phone_number, week_num=week_num, route='outgoing_goal_feedback')
        logger.info(f"Skipping because SendMessage object found for phone number {phone_number.id} and week {week_num}")
    except SendMessage.DoesNotExist:
        send_message_obj = None

    if not send_message_obj:
        message, picklist_json = get_feedback_message(phone_number, week_num)
        logger.info(f"message for {phone_number.id} with language {phone_number.language} is {message}")
        if message:
            SendMessage.objects.create(
                phone_number=phone_number, message=message, route='outgoing_goal_feedback',
                week_num=week_num,picklist=picklist_json,current_weekday=current_weekday,
                message_tracker_col='sent_goal_feedback_message')
            # message_tracker.sent_goal_feedback_message = True
            # message_tracker.save()
            logger.info(f"Goals feedback message sent to {phone_number.id} for week {week_num}")



def handle_final_pilot_message(phone_number, week_num, current_weekday):
    logger.info(f"Handling final pilot message for phone number {phone_number.id}")

    try:
        send_message_obj = SendMessage.objects.get(phone_number=phone_number, week_num=week_num, route='outgoing_final_pilot_message')
        logger.info(f"Skipping because SendMessage object found for phone number {phone_number.id} and week {week_num}")
    except SendMessage.DoesNotExist:
        send_message_obj = None

    if not phone_number.final_pilot_message_sent and not send_message_obj:
        logger.info(f"Final pilot message not yet sent for phone number {phone_number.id}")
        message, include_name = get_final_message(phone_number)
        logger.info(f"Final message for {phone_number.id} with language {phone_number.language} is {message}")
        if message:
            logger.info(f"Creating SendMessage object for phone number {phone_number.id}")
            SendMessage.objects.create(phone_number=phone_number, message=message, 
                route='outgoing_final_pilot_message',week_num=week_num,picklist=None,
                current_weekday=current_weekday,include_name=include_name)
            SendMessage.objects.create(phone_number=phone_number, message=phone_number.post_survey, 
                route='outgoing_post_survey_link',week_num=week_num,picklist=None,
                current_weekday=current_weekday,include_name=False)
            logger.info(f"SendMessage object created for phone number {phone_number.id}")
            # phone_number.final_pilot_message_sent = True
            # phone_number.save()
            logger.info(f"Final pilot message sent to {phone_number.id}")
        else:
            logger.warning(f"No message found for phone number {phone_number.id}")
    else:
        logger.info(f"Final pilot message already sent for phone number {phone_number.id}")


def handle_scheduled_info_messages(phone_number, week_num, current_weekday):
    logger.info(f"Handling scheduled info messages for phone number {phone_number.id}, week {week_num}, day {current_weekday}")
    message_tracker_col = f'sent_info_message_{current_weekday}'
    logger.info(f"Message tracker column: {message_tracker_col}")
    message_tracker = MessageTracker.objects.filter(phone_number=phone_number, week_no=week_num).first()
    logger.info(f"Message tracker: {message_tracker}")

    try:
        send_message_obj = SendMessage.objects.filter(phone_number=phone_number, week_num=week_num, 
                                                      current_weekday=current_weekday, message_tracker_col=message_tracker_col)
        logger.info(f"Skipping because SendMessage object found for phone number {phone_number.id} and week {week_num} and day {current_weekday}")
    except SendMessage.DoesNotExist:
        send_message_obj = None

    if not send_message_obj:
        logger.info(f"Message not yet sent for phone number {phone_number.id}")
        message, include_name, picklist_json, message_tracker_col_updated = send_scheduled_message(phone_number, week_num, current_weekday)
        logger.info(f"Message for {phone_number.id} is {message}")
        if message:
            SendMessage.objects.create(
                phone_number=phone_number, message=message, route='outgoing_scheduled_info',
                week_num=week_num, picklist=picklist_json,current_weekday=current_weekday,
                include_name=include_name, message_tracker_col=message_tracker_col_updated)
            logger.info(f"SendMessage object created for phone number {phone_number.id}")
            # Update the message_tracker to mark the message as sent
            
            logger.info(f"Scheduled info message sent to {phone_number.id} for week {week_num}, day {current_weekday}")
        else:
            logger.warning(f"No message found for phone number {phone_number.id}")
    else:
        logger.info(f"Message already sent for phone number {phone_number.id}")       

    
                    

@shared_task
def send_messages():
    logger.info("Starting send_messages task")
    scheduled_messages = SendMessage.objects.filter(sent=False,route__in=['outgoing_scheduled_info','outgoing_scheduled_goal','outgoing_goal_feedback'])
    logger.info(f"Found {scheduled_messages.count()} scheduled messages to send")
    for message in scheduled_messages:
        logger.info(f"Sending message {message.id} to phone number {message.phone_number.id}")
        success = retry_send_message_vonage(message.message, message.phone_number, message.route, max_retries=3, retry_delay=5)
        if success:
            logger.info(f"Message {message.id} sent successfully")
            message.sent = True
            message.save()
            TextMessage.objects.create(phone_number=message.phone_number, message=message.message, route=message.route)
            MessageTracker.objects.filter(phone_number=message.phone_number, 
                                          week_no=message.week_num).update(**{message.message_tracker_col: True})
            if message.picklist:
                Picklist.objects.create(phone_number=message.phone_number, context=message.route, picklist=message.picklist)
                logger.info(f"Picklist created for message {message.id}")
        else:
            logger.error(f"Failed to send message {message.id}")
    logger.info("Finished send_messages task")   
    #time.sleep(10)


@shared_task
def send_topic_selection_message():
    logger.info("Starting send_topic_selection_message task")
    scheduled_messages = SendMessage.objects.filter(sent=False,route='outgoing_scheduled_topic_selection')
    logger.info(f"Found {scheduled_messages.count()} scheduled topic selection messages to send")
    for message in scheduled_messages:
        logger.info(f"Sending topic selection message {message.id} to phone number {message.phone_number.id}")
        success = retry_send_message_vonage(message.message, message.phone_number, message.route, max_retries=3, retry_delay=5,include_name=message.include_name)
        if success:
            logger.info(f"Topic selection message {message.id} sent successfully")
            message.sent = True
            message.save()
            TextMessage.objects.create(phone_number=message.phone_number, message=message.message, route=message.route)
            MessageTracker.objects.filter(phone_number=message.phone_number, 
                                          week_no=message.week_num).update(**{message.message_tracker_col: True})
            if message.picklist:
                Picklist.objects.create(phone_number=message.phone_number, context=message.route, picklist=message.picklist)
                logger.info(f"Picklist created for message {message.id}")
        else:
            logger.error(f"Failed to send topic selection message {message.id}")
    logger.info("Finished send_topic_selection_message task")
    #time.sleep(10)
                


@shared_task
def send_final_pilot_message():
    logger.info("Starting send_final_pilot_message task")
    scheduled_messages = SendMessage.objects.filter(sent=False,route='outgoing_final_pilot_message')
    logger.info(f"Found {scheduled_messages.count()} scheduled final pilot messages to send")
    for message in scheduled_messages:
        logger.info(f"Sending final pilot message {message.id} to phone number {message.phone_number.id}")
        success = retry_send_message_vonage(message.message, message.phone_number, message.route, max_retries=3, retry_delay=5,include_name=message.include_name)
        if success:
            logger.info(f"Final pilot message {message.id} sent successfully")
            message.sent = True
            message.save()
            TextMessage.objects.create(phone_number=message.phone_number, message=message.message, route=message.route)
            PhoneNumber.objects.filter(id=message.phone_number.id).update(final_pilot_message_sent=True,study_completed=True)
            logger.info(f"PhoneNumber object {message.phone_number.id} updated")
        else:
            logger.error(f"Failed to send final pilot message {message.id}")
    logger.info("Finished send_final_pilot_message task")
    #time.sleep(10)

@shared_task
def send_final_study_survey():
    logger.info("Starting send_final_pilot_message task")
    scheduled_messages = SendMessage.objects.filter(sent=False,route='outgoing_post_survey_link')
    logger.info(f"Found {scheduled_messages.count()} scheduled survey links to send")
    for message in scheduled_messages:
        logger.info(f"Sending final survey link {message.id} to phone number {message.phone_number.id}")
        success = retry_send_message_vonage(message.message, message.phone_number, message.route, max_retries=3, retry_delay=5,include_name=message.include_name)
        if success:
            logger.info(f"Final pilot message {message.id} sent successfully")
            message.sent = True
            message.save()
            TextMessage.objects.create(phone_number=message.phone_number, message=message.message, route=message.route)
            PhoneNumber.objects.filter(id=message.phone_number.id).update(final_pilot_message_sent=True,study_completed=True)
            logger.info(f"PhoneNumber object {message.phone_number.id} updated")
        else:
            logger.error(f"Failed to send final survey link {message.id}")
    logger.info("Finished send_final_study_survey task")
    #time.sleep(10)

# from django.db.models import F
# @shared_task
# def update_futuredate_testing():
#     DayNumber.objects.all().update(day_number=F('day_number') + 1)
#     return None


# from celery import chain
# @shared_task
# def send_messages_chain():
#     chain(update_futuredate_testing.s(),get_messages.s(), send_topic_selection_message.s(),send_messages.s(), send_final_pilot_message.s(), 
#           send_final_study_survey.s())()
#     return None