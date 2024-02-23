import time
import pytz
from datetime import datetime, timezone, timedelta
from base.models import *
from .helper_functions import *

from datetime import datetime, timedelta
from pytz import timezone
logger = logging.getLogger(__name__)
def get_week_num_and_current_weekday(created_at):
    """
    Calculate the number of completed weeks (as full Sundays passed)
    since the created_at date and the current weekday.

    Parameters:
    - created_at (datetime.date or datetime.datetime): The date from which to calculate.

    Returns:
    - tuple: (week_num, current_weekday)
        - week_num (int): Number of Sundays that have passed since created_at.
        - current_weekday (int): The current weekday (1 for Monday, ... 7 for Sunday).
    """
    # Ensure created_at is a datetime.date object
    mst = timezone('America/Denver')
    if isinstance(created_at, datetime):
        created_at = created_at.astimezone(mst)
    
    
    
    today = datetime.now(mst)
    
    # Calculate the current weekday (Python's weekday() returns 0 for Monday, so add 1 to match the desired output)
    current_weekday = today.weekday() + 1
    
    # Adjust the calculation for week_num
    if created_at.weekday() < 6:  # If created_at is not a Sunday
        # Find the next Sunday after created_at
        next_sunday = created_at + timedelta(days=(6 - created_at.weekday()))
    else:
        # If created_at is Sunday, consider that as the first counting point
        next_sunday = created_at
    
    if today >= next_sunday:
        # Calculate the number of complete weeks by counting Sundays
        week_num = (today - next_sunday).days // 7 + 1
    else:
        # If today is before the first Sunday after created_at, no complete week has passed
        week_num = 0
    
    return week_num, current_weekday
    
def get_topic_selection_message(phone_number,week_num):
    logger.info(f"Getting topic selection message for phone number {phone_number.id}, week {week_num}")
    topics_in_weekly_topic = WeeklyTopic.objects.filter(phone_number=phone_number).values_list('topic__id', flat=True)
    logger.info(f"Topics in weekly topic: {topics_in_weekly_topic}")
    topics_not_in_weekly_topic = Topic.objects.exclude(id__in=topics_in_weekly_topic)
    logger.info(f"Topics not in weekly topic: {topics_not_in_weekly_topic}")
    if  phone_number.language == 'es':
        topic_info_not_in_weekly_topic = topics_not_in_weekly_topic.values('id', 'name_es')
        picklist = {str(topic_info['id']): topic_info['name_es'] for topic_info in topic_info_not_in_weekly_topic}
        default_topic_id = min(picklist.keys())
        default_topic_name = picklist[default_topic_id]
        WeeklyTopic.objects.create(phone_number=phone_number, topic_id=default_topic_id, week_number=week_num)
        logger.info(f"Created WeeklyTopic object for phone number {phone_number.id}, topic {default_topic_id}, week {week_num}")
        pre_message = f'Chat del Corazón le enviará mensajes esta semana sobre {default_topic_name}. Si prefiere un tema diferente, escriba el número del tema que prefiere de esta lista:\n'
        if topic_info_not_in_weekly_topic.count()<=1:
            pre_message = f'Chat del Corazón le enviará mensajes esta semana sobre {default_topic_name}.\n'
            message = ""
        else:
            pre_message = f'Chat del Corazón le enviará mensajes esta semana sobre {default_topic_name}. Si prefiere un tema diferente, escriba el número del tema que prefiere de esta lista:\n'
            
            message = '\n'.join([f"{topic_id}. {topic_name}" for topic_id, topic_name in picklist.items() if topic_id != min(picklist.keys())])
        message = pre_message + message
    else:
        topic_info_not_in_weekly_topic = topics_not_in_weekly_topic.values('id', 'name')
        picklist = {str(topic_info['id']): topic_info['name'] for topic_info in topic_info_not_in_weekly_topic}
        default_topic_id = min(picklist.keys())
        default_topic_name = picklist[default_topic_id]
        WeeklyTopic.objects.create(phone_number=phone_number, topic_id=default_topic_id, week_number=week_num)
        logger.info(f"Created WeeklyTopic object for phone number {phone_number.id}, topic {default_topic_id}, week {week_num}")
        if topic_info_not_in_weekly_topic.count()<=1:
            pre_message = f'Chat 4 Heart Health is sending you messages over the next few days about {default_topic_name}.\n'
            message = ""
        else:
            pre_message = f'Chat 4 Heart Health is sending you messages over the next few days about {default_topic_name}. If you prefer a different topic, write the number of the topic you prefer from this list:\n'
            message = '\n'.join([f"{topic_id}. {topic_name}" for topic_id, topic_name in picklist.items() if topic_id != min(picklist.keys())])
        message = pre_message + message
    picklist_json = json.dumps(picklist)
    return message, default_topic_id, picklist_json


def get_goals_message(phone_number,week_num):
    logger.info(f"Getting goals message for phone number {phone_number.id}, week {week_num}")
    weekly_topic_id = WeeklyTopic.objects.filter(phone_number=phone_number,week_number=week_num)[0].topic_id
    logger.info(f"Weekly topic ID: {weekly_topic_id}")
    topic_goals = TopicGoal.objects.filter(topic_id=weekly_topic_id)
    logger.info(f"Found {topic_goals.count()} topic goals")
    if not topic_goals:
        logger.error(f'No goals found for topic {weekly_topic_id}')
        return None, None
    topic_goal = topic_goals[0]
    logger.info(f"Selected topic goal: {topic_goal.id}")
    if phone_number.language == 'es':
        message = topic_goal.goal_es
    else:
        message = topic_goal.goal
    logger.info(f"Message: {message}")
    picklist = topic_goal.goal_dict            
    picklist_json = json.dumps(picklist)
    logger.info(f"Returning message and picklist JSON for phone number {phone_number.id}")
    return message, picklist_json


def get_feedback_message(phone_number,week_num):
    logger.info(f"Getting feedback message for phone number {phone_number.id}, week {week_num}")
    weekly_topic_id = WeeklyTopic.objects.filter(phone_number=phone_number,week_number=week_num)[0].topic_id
    logger.info(f"Weekly topic ID: {weekly_topic_id}")
    topic_goals = TopicGoal.objects.filter(topic_id=weekly_topic_id)
    logger.info(f"Found {topic_goals.count()} topic goals")
    if not topic_goals:
        logger.error(f'No goals found for topic {weekly_topic_id}')
        return None, None
    topic_goal = topic_goals[0]
    logger.info(f"Selected topic goal: {topic_goal.id}")
    if phone_number.language == 'es':
        message = topic_goal.goal_feedback_es
    else:
        message = topic_goal.goal_feedback
    logger.info(f"Message: {message}")
    picklist = topic_goal.goal_feedback_dict
    picklist_json = json.dumps(picklist)
    logger.info(f"Returning message and picklist JSON for phone number {phone_number.id}")
    return message, picklist_json



def send_scheduled_message(phone_number,week_num,current_weekday):
    logger.info(f"Sending scheduled message for phone number {phone_number.id}, week {week_num}, day {current_weekday}")
    weekly_topic_id = WeeklyTopic.objects.filter(phone_number=phone_number,week_number=week_num)[0].topic_id
    logger.info(f"Weekly topic ID: {weekly_topic_id}")
    if phone_number.arm.name.lower().find("ai_chat") != -1:
        scheduled_messages = ScheduledMessage.objects.filter(topic_id=weekly_topic_id,weekday=current_weekday)
    else:
        scheduled_messages = ScheduledMessageControl.objects.filter(topic_id=weekly_topic_id,weekday=current_weekday)
    logger.info(f"Found {scheduled_messages.count()} scheduled messages")

    if not scheduled_messages:
        logger.info(f'No scheduled messages found for topic {weekly_topic_id} and weekday {current_weekday}')
        return None, None, None, None
    
    message_tracker_col = f'sent_info_message_{current_weekday}'
    logger.info(f"Message tracker column: {message_tracker_col}")
    try:
        message_tracker = MessageTracker.objects.filter(phone_number=phone_number, week_no=week_num)[0]
    except IndexError:
        message_tracker = None
    logger.info(f"Message tracker: {message_tracker}")

    if getattr(message_tracker, message_tracker_col):
        logger.info(f'Skipping {phone_number.id} because scheduled info message was sent for week {week_num} and day {current_weekday}')
        return None, None, None, None
    
    scheduled_message = scheduled_messages[0]
    logger.info(f"Selected scheduled message: {scheduled_message.id}")
    if phone_number.language == 'es':
        message = scheduled_message.message_es
    else:
        message = scheduled_message.message
    logger.info(f"Message: {message}")

    if phone_number.arm.name.lower().find("ai_chat") != -1:
        picklist = scheduled_message.picklist
        picklist_json = json.dumps(picklist)
        Picklist.objects.create(phone_number=phone_number, context='regular_picklist', picklist=picklist_json)
        if phone_number.language == 'es':
            numbered_dialog = '\n'.join([f"{i}. {dialog_dict[dialog]}" for i, dialog in convert_str_to_dict(picklist_json).items()])
        else:
            numbered_dialog = '\n'.join([f"{i}. {dialog}" for i, dialog in convert_str_to_dict(picklist_json).items()])
        message = message + '\n' + numbered_dialog
        include_name = True
    else:
        message = message
        include_name = False
        picklist_json = None

    logger.info(f"Returning message, include_name, picklist_json, and message_tracker_col for phone number {phone_number.id}")
    return message, include_name, picklist_json, message_tracker_col


def get_final_message(phone_number):
    logger.info(f"Getting final message for phone number {phone_number.id}")
    if phone_number.language == "es" and phone_number.arm.name == "control":
        logger.info(f"Phone number {phone_number.id} is in control arm and language is Spanish")
        message = settings.FINAL_MESSAGE_CONTROL_ES
        include_name = False
    elif phone_number.language == "es" and phone_number.arm.name != "control":
        logger.info(f"Phone number {phone_number.id} is not in control arm and language is Spanish")
        message = settings.FINAL_MESSAGE_ES
        include_name = True
    elif phone_number.arm.name != "control":
        logger.info(f"Phone number {phone_number.id} is not in control arm and language is not Spanish")
        message = settings.FINAL_MESSAGE
        include_name = True
    else:
        logger.info(f"Phone number {phone_number.id} is in control arm and language is not Spanish")
        message = settings.FINAL_MESSAGE_CONTROL
        include_name = False
    logger.info(f"Returning message and include_name for phone number {phone_number.id}")
    return message, include_name