import time
import pytz
from datetime import datetime, timezone, timedelta
from base.models import *
from .helper_functions import *

def get_week_num_and_current_weekday(created_at):
    mst = timezone(timedelta(hours=-7))
    # Convert the datetime to MST
    created_at = created_at.astimezone(mst)
    # Get current datetime in UTC
    now_utc = datetime.now(pytz.utc)
    # Convert current datetime to the timezone of created_at
    now_in_created_at_tz = now_utc.astimezone(created_at.tzinfo)
    # Calculate the difference in days
    total_days = (now_in_created_at_tz.date() - created_at.date()).days    
    if total_days <= 0:
        return 0, 0
    else:
        week_num = total_days // 5 + 1
        current_weekday = total_days % 5
        if current_weekday == 0:
            week_num -= 1
            current_weekday = 5
        return week_num, current_weekday
    
def get_topic_selection_message(phone_number,week_num):
    topics_in_weekly_topic = WeeklyTopic.objects.filter(phone_number=phone_number).values_list('topic__id', flat=True)
    topics_not_in_weekly_topic = Topic.objects.exclude(id__in=topics_in_weekly_topic)
    if  phone_number.language == 'es':
        topic_info_not_in_weekly_topic = topics_not_in_weekly_topic.values('id', 'name_es')
        picklist = {str(topic_info['id']): topic_info['name_es'] for topic_info in topic_info_not_in_weekly_topic}
        default_topic_id = min(picklist.keys())
        default_topic_name = picklist[default_topic_id]
        WeeklyTopic.objects.create(phone_number=phone_number, topic_id=default_topic_id, week_number=week_num)
        pre_message = f'Chat del Corazón le enviará mensajes en los próximos días sobre una {default_topic_name}. Si prefiere un tema diferente, escriba el número del tema que prefiere de esta lista:\n'
        if topic_info_not_in_weekly_topic.count()<=1:
            pre_message = f'Chat del Corazón le enviará mensajes en los próximos días sobre una {default_topic_name}.\n'
            message = ""
        else:
            pre_message = f'Chat del Corazón le enviará mensajes en los próximos días sobre una {default_topic_name}. Si prefiere un tema diferente, escriba el número del tema que prefiere de esta lista:\n'
            message = '\n'.join([f"{topic_id}. {topic_name}" for topic_id, topic_name in picklist.items() if topic_id != min(picklist.keys())])
        message = pre_message + message
    else:
        topic_info_not_in_weekly_topic = topics_not_in_weekly_topic.values('id', 'name')
        picklist = {str(topic_info['id']): topic_info['name'] for topic_info in topic_info_not_in_weekly_topic}
        default_topic_id = min(picklist.keys())
        default_topic_name = picklist[default_topic_id]
        WeeklyTopic.objects.create(phone_number=phone_number, topic_id=default_topic_id, week_number=week_num)
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
    weekly_topic_id = WeeklyTopic.objects.filter(phone_number=phone_number,week_number=week_num)[0].topic_id
    topic_goals = TopicGoal.objects.filter(topic_id=weekly_topic_id)
    if not topic_goals:
        logger.error(f'No goals found for topic {weekly_topic_id}')
    topic_goal = topic_goals[0]
    if phone_number.language == 'es':
        message = topic_goal.goal_es
    else:
        message = topic_goal.goal
    picklist = topic_goal.goal_dict            
    logger.info(f"Sent goals message to {phone_number.id} for topic {weekly_topic_id}")
    picklist_json = json.dumps(picklist)
    return message, picklist_json

def get_feedback_message(phone_number,week_num):
    weekly_topic_id = WeeklyTopic.objects.filter(phone_number=phone_number,week_number=week_num)[0].topic_id
    topic_goals = TopicGoal.objects.filter(topic_id=weekly_topic_id)
    if not topic_goals:
        logger.error(f'No goals found for topic {weekly_topic_id}')
    topic_goal = topic_goals[0]
    if phone_number.language == 'es':
        message = topic_goal.goal_feedback_es
    else:
        message = topic_goal.goal_feedback
    picklist = topic_goal.goal_feedback_dict
    picklist_json = json.dumps(picklist)
    return message, picklist_json

def send_scheduled_message(phone_number,week_num,current_weekday):
    weekly_topic_id = WeeklyTopic.objects.filter(phone_number=phone_number,week_number=week_num)[0].topic_id
    if phone_number.arm.name.lower().find("ai_chat") != -1:
        scheduled_messages = ScheduledMessage.objects.filter(topic_id=weekly_topic_id,weekday=current_weekday)
    else:
        scheduled_messages = ScheduledMessageControl.objects.filter(topic_id=weekly_topic_id,weekday=current_weekday)

    if not scheduled_messages:
        logger.info(f'No scheduled messages found for topic {weekly_topic_id} and weekday {current_weekday}')
        return None, None, None, None
    
    message_tracker_col = f'sent_info_message_{current_weekday}'
    try:
        message_tracker = MessageTracker.objects.filter(phone_number=phone_number, week_no=week_num)[0]
    except IndexError:
        message_tracker = None
    logger.info(f"message tracker column to be updated: {message_tracker_col}")
    if getattr(message_tracker, message_tracker_col):
        logger.info(f'Skipping {phone_number.id} because scheduled info message was sent for week {week_num} and day {current_weekday}')
        return None, None, None, None
    
    scheduled_message = scheduled_messages[0]
    if phone_number.language == 'es':
        message = scheduled_message.message_es
    else:
        message = scheduled_message.message

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

    return message, include_name, picklist_json, message_tracker_col

def get_final_message(phone_number):
    if phone_number.language == "es" and phone_number.arm.name == "control":
        message = settings.FINAL_MESSAGE_CONTROL_ES
        include_name = False
    elif phone_number.language == "es" and phone_number.arm.name != "control":
        message = settings.FINAL_MESSAGE_ES
        include_name = True
    elif phone_number.arm.name != "control":
        message = settings.FINAL_MESSAGE
        include_name = True
    else:
        message = settings.FINAL_MESSAGE_CONTROL
        include_name = False
    return message, include_name